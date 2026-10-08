# AMA Specify Extension List

`ama-specify` is an independently packaged, read-only subset of Spec Kit
functionality for inspecting AMA-local extensions. It lists installed extension
metadata and, when explicitly requested, validated project catalog entries.

The package exposes these entry points:

```text
ama-specify extension list
python -m specify_cli extension list
```

It does not install, activate, repair, enable, disable, or remove extensions.
It does not provide a `specify` console script, import an upstream `specify`
package, modify another checkout, or shadow an existing Spec Kit installation.

Runtime work is delegated to the package daemon over owner-authenticated local
IPC. Local development accepts only authorized synthetic fixtures. Normal
non-synthetic operation and qualifying validation require the separately
governed sovereign runtime described by the repository feature contract.
