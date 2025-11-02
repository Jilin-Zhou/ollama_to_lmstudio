import os
import json
from pathlib import Path

# ========== 配置部分 ==========
# 根据实际情况写文件位置
manifest_dir = Path(r"D:\AI\Ollama\manifests\registry.ollama.ai")
blob_dir = Path(r"D:\AI\Ollama\blobs")
publicModels_dir = Path(r"D:\llm_model")
lmstudio_dir = publicModels_dir / "lmstudio"
bridge_dir = lmstudio_dir / "ollama_bridge"

# ========== 打印目录 ==========
print("\n=== Confirming Directories ===\n")
print(f"Manifest Directory: {manifest_dir}")
print(f"Blob Directory: {blob_dir}")
print(f"LMStudio Directory: {lmstudio_dir}")
print(f"Ollama Bridge Directory: {bridge_dir}")

# ========== 检查并创建目标目录 ==========
if not publicModels_dir.exists():
    publicModels_dir.mkdir(parents=True, exist_ok=True)
    print("\nPublic Models Directory Created.")
else:
    print("\nPublic Models Directory Confirmed.")

if not lmstudio_dir.exists():
    lmstudio_dir.mkdir(parents=True, exist_ok=True)
    print("LMStudio Directory Created.")

if not bridge_dir.exists():
    bridge_dir.mkdir(parents=True, exist_ok=True)
    print("Ollama Bridge Directory Created.")
else:
    print("Ollama Bridge Directory Exists, will update existing links.\n")

# ========== 扫描 manifest 文件 ==========
print("\nExploring Manifest Directory:\n")
manifestLocations = [p for p in manifest_dir.rglob("*") if p.is_file()]

print(f"Found {len(manifestLocations)} manifest files.\n")

# ========== 解析每个 manifest ==========
for manifest in manifestLocations:
    try:
        with open(manifest, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception as e:
        print(f"Failed to read manifest {manifest}: {e}")
        continue

    modelConfig = modelFile = None

    # config digest
    if "config" in obj and "digest" in obj["config"]:
        digest = obj["config"]["digest"].replace("sha256:", "sha256-")
        modelConfig = blob_dir / digest

    # 遍历 layers
    for layer in obj.get("layers", []):
        media = layer.get("mediaType", "")
        digest = layer.get("digest", "").replace("sha256:", "sha256-")
        if media.endswith("model"):
            modelFile = blob_dir / digest

    if not modelConfig or not modelFile:
        continue  # 跳过不完整的 manifest

    # 解析 config 文件
    try:
        with open(modelConfig, "r", encoding="utf-8") as f:
            modelConfigObj = json.load(f)
    except Exception as e:
        print(f"Failed to read {modelConfig}: {e}")
        continue

    modelQuant = modelConfigObj.get("file_type", "unknown")
    modelExt = modelConfigObj.get("model_format", "bin")
    modelTrainedOn = modelConfigObj.get("model_type", "unknown")

    # 模型名称 = manifest 上级目录名
    modelName = manifest.parent.name

    print(f"\n--- Processing Model: {modelName} ---")
    print(f"Quant: {modelQuant}")
    print(f"Extension: {modelExt}")
    print(f"Trained On: {modelTrainedOn}")

    model_out_dir = bridge_dir / modelName
    model_out_dir.mkdir(parents=True, exist_ok=True)

    link_name = (
        model_out_dir
        / f"{modelName}-{modelTrainedOn}-{modelQuant}.{modelExt}"
    )

    # 删除旧链接（仅同名文件）
    if link_name.exists() or link_name.is_symlink():
        link_name.unlink()

    print(f"Creating symbolic link → {link_name.name}")
    try:
        os.symlink(modelFile, link_name)
    except (OSError, NotImplementedError):
        # Windows fallback: use mklink
        os.system(f'mklink "{link_name}" "{modelFile}"')

print("\n*********************")
print("Ollm Bridge Safe Complete")
print(f"Add the following directory to LM Studio if not already added:\n{bridge_dir}")
