# Research and decisions

- **Decision:** Use the current voiceover report and narration authoring route. **Reason:** Both already own script review; a second catalogue or approval workflow would split decisions. **Alternative:** A new standalone script system.
- **Decision:** Treat the Reel's long/short suggestion as advisory. **Reason:** A fixed five-word alternation can damage conversational Kannada-English, complex explanations, and meaningful natural sound. **Alternative:** A hard sentence-length gate.
- **Decision:** Analyze ordered cue text in one Python module. **Reason:** Vlog tooling is Python and code-driven narration already invokes Python for speech; a normalized cue contract avoids duplicate text heuristics. **Alternative:** Separate language-specific analyzers.
