# Safari MOV playback gesture

Reported on iPhone Safari: source MOV playback can reject after asynchronous loading when the original picker gesture has expired. The composer now loads first, then requires an explicit tap to start source playback and capture, and a second tap to replay and verify the recorded MP4. Both play calls and AudioContext.resume run on the respective click stack. Audio stays routed locally and validation still rejects silence. Existing preview poster and authenticated transfer recovery are retained.

The regression enforces synchronous click-only playback in Chrome and checks the real Timeline attachment path and cancellation. iPhone Safari device verification is required before production promotion.

## Automatic preparation candidate

Attachment selection first tries local remux of compatible H.264/HEVC and AAC MOV files. It preserves sample offsets and payload, normalizes MOV container/AAC headers, verifies a decoded video frame and decodes output PCM offline. Noncompatible containers or devices use the existing verified two-gesture conversion. No file is uploaded until the existing post action.
