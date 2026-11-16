# Safari MOV playback gesture

Reported on iPhone Safari: source MOV playback can reject after asynchronous loading when the original picker gesture has expired. The composer now loads first, then requires an explicit tap to start source playback and capture, and a second tap to replay and verify the recorded MP4. Both play calls and AudioContext.resume run on the respective click stack. Audio stays routed locally and validation still rejects silence. Existing preview poster and authenticated transfer recovery are retained.

The regression enforces synchronous click-only playback in Chrome and checks the real Timeline attachment path and cancellation. iPhone Safari device verification is required before production promotion.
