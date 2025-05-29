import os

import modal
from dotenv import load_dotenv


def get_recommended_env_vars() -> dict[str, str]:
    recommended_vars = [
        "JUPYTER_PASSWORD",
        "HUGGINGFACE_TOKEN",
        "CIVITAI_TOKEN",
    ]
    env_vars = {var: os.environ.get(var, "") for var in recommended_vars}
    if not env_vars["HUGGINGFACE_TOKEN"]:
        print(
            "WARNING: Environment variable 'HUGGINGFACE_TOKEN' is not defined. "
            "You may not be able to download models from Hugging Face."
        )

    if not env_vars["CIVITAI_TOKEN"]:
        print(
            "WARNING: Environment variable 'CIVITAI_TOKEN' is not defined. "
            "You may not be able to download models from CivitAI."
        )

    if not env_vars["JUPYTER_PASSWORD"]:
        print(
            "WARNING: Environment variable 'JUPYTER_PASSWORD' is not defined. "
            "Your Jupyter Lab server will not be password protected, which could lead to unauthorized access."
        )

    return env_vars

load_dotenv()
env_vars = get_recommended_env_vars()
custom_image = (
    modal.Image.from_registry("jaezred/runpod-tools:release") # pyright: ignore[reportUnknownMemberType]
    .env(env_vars)
    .pip_install("python-dotenv==1.1.0") # Workaround for modal raising error at container startup
    .run_commands("cd /workspace") # Workaround for modal not having its entrypoint in the Docker WORKDIR
)
app = modal.App()


@app.function(image=custom_image, gpu="L40S")
def run_custom_container() -> None:
    import os
    import subprocess
    print("Running inside custom Docker container!")

    # Forward Jupyter Lab and ComfyUI ports
    with modal.forward(8888) as jupyter_tunnel, modal.forward(8188) as comfyui_tunnel:
        import os
        import subprocess
        print(f"Jupyter Lab tunnel URL: {jupyter_tunnel.url}")
        print(f"ComfyUI tunnel URL: {comfyui_tunnel.url}")
        print("Tunnels are active. Your services should be accessible if running in the container.")

        # Set RUNPOD_POD_ID if not present (for local/Modal runs)
        env = os.environ.copy()
        if "RUNPOD_POD_ID" not in env:
            env["RUNPOD_POD_ID"] = "modal-local"

        # Launch Jupyter Lab with the same arguments as in Dockerfile
        jupyter_cmd = [
            "jupyter", "lab",
            "--ip=0.0.0.0",
            "--port=8888",
            "--allow-root",
            "--no-browser",
            "--FileContentsManager.delete_to_trash=False",
            "--ServerApp.root_dir=/workspace",
            "--ServerApp.preferred_dir=/workspace",
            f"--ServerApp.token={env.get('JUPYTER_PASSWORD', '')}",
            f"--ServerApp.allow_origin=https://{env['RUNPOD_POD_ID']}-8888.proxy.runpod.net",
        ]
        subprocess.run(jupyter_cmd, env=env, check=True)


@app.local_entrypoint()
def main():
    run_custom_container.remote()
