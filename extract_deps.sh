#!/bin/bash
set -e

uv sync
if [ ! -d ComfyUI ]; then
  uv run comfy --workspace=ComfyUI --skip-prompt install --skip-requirement --skip-manager --cpu
fi

if [ ! -d ComfyUI/custom_nodes/ComfyUI-Manager ]; then
  git -C ComfyUI/custom_nodes clone https://github.com/ltdrdata/ComfyUI-Manager.git
fi


for workflow_file in workflows/*_workflow.json; do
    workflow_basename=$(basename "$workflow_file")
    prefix="${workflow_basename%_workflow.json}"
    deps_file="workflow_deps/"$prefix"_deps.json"
    echo $deps_file
    uv run comfy --here node deps-in-workflow --workflow $workflow_file --output $deps_file
done