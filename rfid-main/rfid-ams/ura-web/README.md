# ura-web

Browser version of SparkFun's Universal Reader Assistant for the M7E module. Needs Chrome or Edge (Web Serial).

## Run

    cd ura-web
    python3 -m http.server 8080

Open http://localhost:8080, click **Connect reader** and pick the serial port, or click **Demo mode** to try it with a fake reader.

## Test

    npm test

## Notes
- Writes and locks are off until you tick "Enable writes" on the Tag memory tab.
- Firmware update, kill and permanent locks are intentionally not available.
- The Log tab records every byte sent and received; download it when reporting a problem.
