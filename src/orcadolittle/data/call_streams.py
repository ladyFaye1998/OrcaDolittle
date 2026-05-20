"""Tokenisation, batching, and MLM masking for per-encounter call-ID streams.

A *call-ID stream* is a single encounter, represented as the ordered list of
discrete call-type identifiers emitted by the focal group during that
encounter. This module is intentionally agnostic to whether the call IDs come
from DCLDE 2026 annotations
(``orcadolittle.data.dclde_loader.load_dclde_streams``) or from the synthetic
generator (``orcadolittle.data.synthetic.make_synthetic_streams``); both
produce ``list[list[int]]`` in the same vocabulary space.

Convention
----------
Vocabulary IDs ``0..NUM_SPECIAL-1`` are reserved for special tokens. Call-type
IDs start at ``NUM_SPECIAL``. Sequences are stored as Python ``list[int]``
during construction, then padded to a single tensor at batching time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import torch
from torch.utils.data import Dataset


SPECIAL_TOKENS = ("[PAD]", "[BOS]", "[EOS]", "[MASK]", "[UNK]")
PAD_ID = 0
BOS_ID = 1
EOS_ID = 2
MASK_ID = 3
UNK_ID = 4
NUM_SPECIAL = len(SPECIAL_TOKENS)


@dataclass
class Vocab:
    """Mapping from string call-type labels to integer IDs.

    Special tokens occupy the first ``NUM_SPECIAL`` slots. Call types are
    assigned IDs in insertion order; this keeps the vocabulary deterministic
    given the same input order.
    """

    call_types: tuple[str, ...]

    def __post_init__(self) -> None:
        if any(t in SPECIAL_TOKENS for t in self.call_types):
            raise ValueError("call_types must not collide with special tokens")
        if len(set(self.call_types)) != len(self.call_types):
            raise ValueError("call_types must be unique")
        self._lookup = {t: NUM_SPECIAL + i for i, t in enumerate(self.call_types)}

    @property
    def size(self) -> int:
        return NUM_SPECIAL + len(self.call_types)

    def encode(self, calls: Iterable[str]) -> list[int]:
        return [self._lookup.get(c, UNK_ID) for c in calls]

    def decode(self, ids: Iterable[int]) -> list[str]:
        out: list[str] = []
        for i in ids:
            if i < NUM_SPECIAL:
                out.append(SPECIAL_TOKENS[i])
            else:
                idx = i - NUM_SPECIAL
                out.append(self.call_types[idx] if 0 <= idx < len(self.call_types) else "[UNK]")
        return out

    @classmethod
    def from_streams(cls, streams: Iterable[Sequence[str]]) -> "Vocab":
        seen: list[str] = []
        seen_set: set[str] = set()
        for s in streams:
            for c in s:
                if c not in seen_set:
                    seen.append(c)
                    seen_set.add(c)
        return cls(call_types=tuple(seen))


class CallStreamDataset(Dataset):
    """Holds tokenised per-encounter call-ID streams.

    Each item is a 1-D ``torch.LongTensor`` of length ``2 + min(len(stream), max_len-2)``,
    with ``[BOS]`` prepended and ``[EOS]`` appended. Streams longer than
    ``max_len - 2`` are truncated at the head; streams shorter than 2 raw
    tokens are dropped at construction time.
    """

    def __init__(
        self,
        streams: Sequence[Sequence[int]],
        max_len: int = 256,
        min_len: int = 2,
    ) -> None:
        if max_len < 4:
            raise ValueError("max_len must be at least 4 to fit [BOS] tok tok [EOS]")
        self.max_len = max_len
        self.min_len = min_len
        self._items: list[torch.Tensor] = []
        for s in streams:
            if len(s) < min_len:
                continue
            trimmed = list(s)[: max_len - 2]
            tokens = [BOS_ID, *trimmed, EOS_ID]
            self._items.append(torch.tensor(tokens, dtype=torch.long))

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, idx: int) -> torch.Tensor:
        return self._items[idx]


def collate_call_streams(batch: Sequence[torch.Tensor]) -> dict[str, torch.Tensor]:
    """Right-pad a batch of variable-length call streams.

    Returns a dict with:
      * ``input_ids``: ``(B, L)`` LongTensor, padded with ``PAD_ID``.
      * ``attention_mask``: ``(B, L)`` BoolTensor, ``True`` at non-pad positions.
    """
    max_len = max(int(x.shape[0]) for x in batch)
    input_ids = torch.full((len(batch), max_len), PAD_ID, dtype=torch.long)
    attention_mask = torch.zeros((len(batch), max_len), dtype=torch.bool)
    for i, seq in enumerate(batch):
        n = int(seq.shape[0])
        input_ids[i, :n] = seq
        attention_mask[i, :n] = True
    return {"input_ids": input_ids, "attention_mask": attention_mask}


def mlm_mask(
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    vocab_size: int,
    mask_prob: float = 0.15,
    replace_mask_prob: float = 0.8,
    replace_random_prob: float = 0.1,
    generator: torch.Generator | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Apply BERT-style MLM masking.

    Selects ``mask_prob`` of non-special, non-pad positions for prediction.
    Of those, ``replace_mask_prob`` become ``[MASK]``, ``replace_random_prob``
    become a uniformly random non-special token, and the remainder are left
    unchanged.

    Returns:
      ``(masked_input_ids, labels)`` where ``labels`` is ``-100`` everywhere
      the loss should be ignored, and the original token ID where it should
      be predicted. This is the standard convention for
      ``torch.nn.CrossEntropyLoss(ignore_index=-100)``.
    """
    if not (0.0 <= mask_prob <= 1.0):
        raise ValueError("mask_prob must be in [0, 1]")
    if not (0.0 <= replace_mask_prob + replace_random_prob <= 1.0):
        raise ValueError("replace_mask_prob + replace_random_prob must be <= 1")
    device = input_ids.device
    eligible = attention_mask & (input_ids >= NUM_SPECIAL)
    rand = torch.rand(input_ids.shape, device=device, generator=generator)
    mask_positions = eligible & (rand < mask_prob)

    labels = torch.full_like(input_ids, fill_value=-100)
    labels[mask_positions] = input_ids[mask_positions]

    masked = input_ids.clone()
    role = torch.rand(input_ids.shape, device=device, generator=generator)
    do_mask = mask_positions & (role < replace_mask_prob)
    do_random = mask_positions & (role >= replace_mask_prob) & (
        role < replace_mask_prob + replace_random_prob
    )
    masked[do_mask] = MASK_ID
    if do_random.any():
        rand_tokens = torch.randint(
            low=NUM_SPECIAL,
            high=vocab_size,
            size=(int(do_random.sum().item()),),
            device=device,
            generator=generator,
        )
        masked[do_random] = rand_tokens
    return masked, labels
