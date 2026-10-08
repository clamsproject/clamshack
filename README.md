# ClamShack

You are now in the ClamShack, a tool for running CLAMS applications and managing resulting MMIF files.

Installation:

```bash
pip install -e .[dev]
pip install packages/mmif_storage_mv-0.2.0rc5.tar.gz
```

🗒 At the moment, installation is aimed mostly at developers. It will be streamlined once there is a reliable installable package. The above will allow you to use the ClamShack though, even if you have no interest in developing.

See [docs/clamshack-manual.md](docs/clamshack-manual.md) on how to work with the tool.

To run the tests just type `pytest`.
