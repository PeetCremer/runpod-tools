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
docker build --platform=linux/amd64 -t runpod-tools:latest .
```

This will create a Docker image named `runpod-tools:latest` using the default dependencies specified in the repository. You do not need to modify any files or add custom workflows for this basic build.

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
   docker build --platform=linux/amd64 -t runpod-tools:latest .
   ```

Your custom Docker image is now ready to use, with all the dependencies needed for your specific ComfyUI workflows.

### Running / Using the Docker Container

When you start the Docker container, it will automatically launch a Jupyter Lab server, accessible on port `8888`. This environment is designed to make it easy to interact with ComfyUI and manage your workflows.

**Recommended environment variables:**

- `JUPYTER_PASSWORD`: Set this to password-protect your Jupyter Lab server.  
- `HUGGINGFACE_TOKEN` and `CIVITAI_TOKEN`: Provide your tokens to enable seamless downloading of model files from Hugging Face and CivitAI.

**How to run the container:**

```sh
docker run -p 8888:8888 \
  -e JUPYTER_PASSWORD=yourpassword \
  -e HUGGINGFACE_TOKEN=your_hf_token \
  -e CIVITAI_TOKEN=your_civitai_token \
  runpod-tools:latest
```

**Features:**

- The working directory in Jupyter Lab includes the `run_comfy.ipynb` notebook.  
  Open and run this notebook to start ComfyUI directly within the container.
- By providing your Hugging Face and CivitAI tokens, you can easily download and use the latest image and video generation models.

**Security note:**  
Always set a strong password for `JUPYTER_PASSWORD` to prevent unauthorized access to your Jupyter Lab server.
