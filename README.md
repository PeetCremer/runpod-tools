# runpod-tools

This repository contains tools to run ComfyUI effectively on different GPU platforms such as:
- https://www.runpod.io/ 
- https://modal.com/
- https://vast.ai/

It has a focus on video and image generation with ComfyUI, but can also be used with other models.

## Docker container
The main artifact of this project is a docker container that can run ComfyUI and already contains the dependencies for popular image and video generation models.

### Building the docker container with default dependencies

To build the Docker container with the default set of dependencies (suitable for most ComfyUI image and video generation tasks), simply run:

```sh
docker build --platform=linux/amd64 -t runpod-tools:release .
```

This will create a Docker image named `runpod-tools:release` using the default dependencies specified in the repository. You do not need to modify any files or add custom workflows for this basic build.

### Building the docker container with your dependencies

If you want to use custom ComfyUI workflows or require additional Python packages, you can build a Docker container tailored to your specific needs. This process ensures that all dependencies required by your workflows are included in the final image.

**Steps:**

1. **Install development dependencies**  
   Make sure all development dependencies are installed locally by running:
   ```sh
   uv sync
   ```

2. **Add your ComfyUI workflow files**  
   Place any ComfyUI `.json` workflow files that you want to analyze for dependencies into the `./workflow` directory.

3. **Extract workflow dependencies**  
   Run the provided script to automatically extract the required Python packages from your workflow files:
   ```sh
   ./extract_deps.sh
   ```
   This will generate a list of dependencies in the `./workflow_deps` directory.

4. **Build your custom Docker image**  
   Now, build the Docker container. It will include both the default and your workflow-specific dependencies:
   ```sh
   docker build --platform=linux/amd64 -t runpod-tools:release .
   ```

Your custom Docker image is now ready to use, with all the dependencies needed for your specific ComfyUI workflows.

### Running / Using the Docker Container

When you start the Docker container, it will automatically launch a Jupyter Lab server, accessible on port `8888`. This environment is designed to make it easy to interact with ComfyUI and manage your workflows.

**Recommended environment variables:**

- `JUPYTER_PASSWORD`: Set this to password-protect your Jupyter Lab server.  
- `HUGGINGFACE_TOKEN` and `CIVITAI_TOKEN`: Provide your tokens to enable seamless downloading of model files from Hugging Face and CivitAI.
- `COMFY_MODEL_ENVS`: Optional comma-separated list of model environments to pre-download (for example: `flux,pony,wan`).

**How to run the container:**

Using a `.env` file (recommended): put your tokens and options in a `.env` file in the project root, then run:

```sh
./run_docker.sh
```

The script loads `.env` and forwards `JUPYTER_PASSWORD`, `HUGGINGFACE_TOKEN`, `CIVITAI_TOKEN`, `COMFY_MODEL_ENVS`, and optionally `RUNPOD_POD_ID` into the container. See [run_docker.sh](run_docker.sh).

Or pass variables explicitly:

```sh
docker run -p 8888:8888 \
  -e JUPYTER_PASSWORD=yourpassword \
  -e HUGGINGFACE_TOKEN=your_hf_token \
  -e CIVITAI_TOKEN=your_civitai_token \
  -e COMFY_MODEL_ENVS=flux,pony,wan \
  jaezred/runpod-tools:release
```

**Features:**

- The working directory in Jupyter Lab includes the `run_comfy.ipynb` notebook.  
  Open and run this notebook to start ComfyUI directly within the container.
- By providing your Hugging Face and CivitAI tokens, you can easily download and use the latest image and video generation models.
- By setting `COMFY_MODEL_ENVS`, the container will automatically download the models for the specified environments on startup using `aria2c`. If this variable is not set, the container behaves as before and does not perform any automatic downloads.

**Security note:**  
Always set a strong password for `JUPYTER_PASSWORD` to prevent unauthorized access to your Jupyter Lab server.

## Running on Modal

You can also run the ComfyUI environment using [Modal](https://modal.com/), which provides GPU-backed cloud execution with easy port forwarding for Jupyter Lab and ComfyUI.

### Prerequisites
- Ensure you have [Modal's Python SDK](https://modal.com/docs/guide/getting-started) installed (`uv sync` first).
- Set the following environment variables, either in your shell or in a `.env` file in the project root:
  - `JUPYTER_PASSWORD`: Password to protect your Jupyter Lab server (required)
  - `HUGGINGFACE_TOKEN`: (optional, for downloading models from Hugging Face)
  - `CIVITAI_TOKEN`: (optional, for downloading models from CivitAI)
  - `COMFY_MODEL_ENVS`: (optional, comma-separated list such as `flux,pony,wan` for automatic model downloads inside the Modal container)

### How to run the Modal app

```sh
modal run modal_app.py
```

This will launch the Modal app using the `runpod-tools:release` Docker image from Docker Hub. When running, it will print tunnel URLs for both Jupyter Lab and ComfyUI, for example:

```
Jupyter Lab tunnel URL: https://...modal.run
ComfyUI tunnel URL: https://...modal.run
Tunnels are active. Your services should be accessible if running in the container.
```

Open the Jupyter Lab tunnel URL in your browser and log in with your password. The working directory includes the `run_comfy.ipynb` notebook, which you can use to start ComfyUI directly within the Modal environment.

If you set `COMFY_MODEL_ENVS` before running the app, the same automatic model download step described above will run inside the Modal container as well.

**Note:** Always set a strong password for `JUPYTER_PASSWORD` to prevent unauthorized access to your Jupyter Lab server.
