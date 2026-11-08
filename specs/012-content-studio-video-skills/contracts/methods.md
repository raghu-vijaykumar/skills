# Method selection contract

Each operation skill lists its working methods in `methods.json`. A supported method has one exact script entrypoint and stated inputs, outputs, and review criterion. Different implementations use different scripts, even if they share lower-level helpers. A future method is explicitly unsupported and has no executable script claim.

Before production editing, the workflow precheck records the operation skill, method ID, exact script and arguments, input hashes, expected output, estimate, fallback, and review criterion. The approved plan governs execution; a method or argument change requires new approval. Each operation records FIX, SKIP, REVIEW, or UNSUPPORTED with exact-output evidence.
