"""BERT-style Transformer masked-language-model over call-ID streams.

This is head H3 of the locked architecture in ``docs/ai_architecture.md``.
Default hyperparameters mirror that file:

  * 6 transformer encoder layers
  * 8 attention heads
  * ``d_model = 512``
  * feedforward dim ``4 * d_model``
  * sinusoidal positional encoding, max sequence length 256

The model exposes a standard MLM forward signature: it takes a batch of
``input_ids`` and an ``attention_mask`` and returns per-position logits over
the vocabulary. The training loop computes the masked-language-model loss
against ``labels`` produced by ``orcadolittle.data.call_streams.mlm_mask``.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import torch
from torch import nn


@dataclass
class SequenceLMConfig:
    vocab_size: int
    d_model: int = 512
    n_layers: int = 6
    n_heads: int = 8
    d_ff: int | None = None
    max_len: int = 256
    dropout: float = 0.1
    tie_weights: bool = True

    def __post_init__(self) -> None:
        if self.d_ff is None:
            self.d_ff = 4 * self.d_model
        if self.d_model % self.n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads")
        if self.max_len < 4:
            raise ValueError("max_len must be at least 4")


class _SinusoidalPositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int) -> None:
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float)
            * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0), persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.shape[1]]


class SequenceLM(nn.Module):
    def __init__(self, cfg: SequenceLMConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.embed = nn.Embedding(cfg.vocab_size, cfg.d_model)
        self.pos = _SinusoidalPositionalEncoding(cfg.d_model, cfg.max_len)
        self.dropout = nn.Dropout(cfg.dropout)
        layer = nn.TransformerEncoderLayer(
            d_model=cfg.d_model,
            nhead=cfg.n_heads,
            dim_feedforward=cfg.d_ff,
            dropout=cfg.dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=cfg.n_layers)
        self.norm = nn.LayerNorm(cfg.d_model)
        self.head = nn.Linear(cfg.d_model, cfg.vocab_size, bias=False)
        if cfg.tie_weights:
            self.head.weight = self.embed.weight
        self.apply(self._init_weights)

    @staticmethod
    def _init_weights(module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def num_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """Return per-position vocabulary logits.

        Parameters
        ----------
        input_ids:
            ``(B, L)`` LongTensor of token IDs (possibly with ``[MASK]``).
        attention_mask:
            ``(B, L)`` BoolTensor, ``True`` at real positions, ``False`` at
            pad positions.

        Returns
        -------
        logits:
            ``(B, L, vocab_size)`` FloatTensor.
        """
        if input_ids.shape[1] > self.cfg.max_len:
            raise ValueError(
                f"sequence length {input_ids.shape[1]} exceeds max_len {self.cfg.max_len}"
            )
        x = self.embed(input_ids) * math.sqrt(self.cfg.d_model)
        x = self.pos(x)
        x = self.dropout(x)
        key_padding_mask = ~attention_mask
        x = self.encoder(x, src_key_padding_mask=key_padding_mask)
        x = self.norm(x)
        return self.head(x)
