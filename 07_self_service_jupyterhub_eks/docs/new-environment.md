# Adding a New Notebook Environment

1. Create a folder under `examples/repo2docker/<env-name>` with a `Dockerfile` and `requirements.txt`.
2. Submit a Pull Request with the new folder and a brief README describing the packages.
3. After merge, rebuild the image using `repo2docker`:
   ```bash
   jupyter-repo2docker examples/repo2docker/<env-name>
   ```
4. Update `helm/values.yaml` `profileList` to reference the new image tag.
