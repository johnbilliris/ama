# Container build architecture

- ALL local image builds MUST target only `linux/arm64`, including application,
  job, test, preparation and Dev Container images. Never build local AMD64 or
  multi-platform images, even for later Azure deployment or under emulation.
- Use `docker buildx bake -f docker-bake.json` for all local images, or select
  named targets. Compose and Dev Container builds also pin ARM64.
- Every manual local `docker build` or `docker buildx build` command MUST include
  `--platform linux/arm64`; never rely on the host or builder default or override
  a local target's platform. Keep application Dockerfiles architecture-neutral.
- Azure Container Apps deployment images remain `linux/amd64` and MUST be built
  remotely in ACR or native hosted CI, never on the local workstation. Preserve
  `remoteBuild: true` and the deployment platform in `azure.yaml`. Local ARM64
  images are not deployment artifacts for Container Apps.
- Preserve historical build evidence and deployed image digests truthfully.
  Do not rebuild, replace, delete or redeploy existing images merely to apply
  this forward-looking local-build requirement.
