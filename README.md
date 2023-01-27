# Sequencer Blacklist tools

Due to how the Ethereum KZG-Ceremony Sequencer is constructed, it doesn't actually have a notion of a "blacklist" instead people are marked as having contributed. This tool is to help calculate who has "contributed" but is not in `transcript.json` as an effective blacklist.


## Running:

1. Get the currrent list of contributions from the sequencer:
    `sqlite3 -json /data/kzg-sequencer/storage.sqlite "select * from contributors;" ".exit" > contributions.json`
2. Fetch the latest transcript:
    `wget https://seq.ceremony.ethereum.org/info/current_state -O transcript.json`
3. Run the script:
    `python3 main.py`

