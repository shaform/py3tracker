# py3tracker

Tracking GitHub repositories that don't support Python 3 so we could send pull requests.

## What if a project being listed actually supports Python 3?

py3tracker uses [caniusepython3](https://github.com/brettcannon/caniusepython3) to detect Python 3 compatibility. Please read [their FAQ](https://github.com/brettcannon/caniusepython3/blob/master/README.md) to see possible causes that the project is incorrectly detected as Python 2 only. Another possiblity is that the py3tracker page has not been updated lately and does not reflect the current situation.
