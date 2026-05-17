# Two-minute video script

Total length: **120 seconds**. Single voiceover, four-act structure, dark-editorial title cards in the OrcaDolittle palette.

## Act 1 — The problem (0:00 – 0:25)

*[Black. White text fades in: "The Coller-Dolittle Prize asks for measurable response from animals to broadcasted signals."]*

**VO.** "The Coller-Dolittle Prize doesn't ask us to *decode* an animal's language. It asks us to *talk back* to one — and prove the animal responded.

Almost all bioacoustic AI today does only half of that loop: listen, classify, decode.

Almost nothing builds the other half: pick what to say, predict the response, and ship the system."

*[Cut to underwater shot of orcas, dialect spectrogram overlaying.]*

## Act 2 — The species (0:25 – 0:45)

**VO.** "Killer whales are the only cetacean where the full loop is buildable today on public data alone.

They have stable dialects, ecotype-specific repertoires, and a publicly annotated quarter-million-call dataset released in 2025. They have twenty years of published playback experiments documenting their responses to conspecific calls.

So we built a Doctor Dolittle stack for them."

## Act 3 — The stack (0:45 – 1:35)

*[Animated architecture diagram fading in component by component, each labelled with a single sentence.]*

**VO.** "Four components.

*Perceive.* An audio recording in, ecotype, dialect, and behavioural context out — with calibrated uncertainty.

*Generate.* A conditional generator synthesises candidate calls inside the target population's natural repertoire.

*Select.* A contextual bandit picks the next call to broadcast, trained off-policy on every published killer-whale playback experiment we could find.

*Anticipate.* For every choice, we predict the response *and* the response to two counterfactual stimuli — shuffled and scrambled. If the predictions are too close, we flag the trial."

*[The four components animate into a closed-loop diagram with a hydrophone in and a broadcast-ready waveform out.]*

## Act 4 — The deliverable (1:35 – 2:00)

**VO.** "OrcaDolittle is open-source, MIT-licensed, and shipped as a Docker container.

A field team clones the repo, mounts a hydrophone, and the loop runs.

We don't claim to have proved interspecies communication. We claim to have built the AI half of a Doctor Dolittle pass — and to have made everything except the broadcast itself plug-and-play."

*[OrcaDolittle logo and the prize criteria mapping flashing once, GitHub URL on screen.]*

---

## Production notes

- Title font: Lora 500.
- Palette: `#0d1117` background, `#c9a84c` accent, `#e8e0d4` text.
- Audio: real orca call samples spliced under VO at low volume; no music.
- Subtitles: hard-burned in English; SRT supplied for reviewers.
