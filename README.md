# ClamShack

You are now in the ClamShack, a tool for running CLAMS applications and managing resulting MMIF files.

Installation:

```bash
pip install -r requirements.txt
pip install packages/mmif_storage_mv-0.2.0rc1.tar.gz
cp src/.env.sample src/.env
```

Creating a shack:


See [docs/clamshack-manual.md](docs/clamshack-manual.md) on how to work with the tool.

To run the tests do the following:

```bash
pip install -e .
pip install pytest
pytest
```
