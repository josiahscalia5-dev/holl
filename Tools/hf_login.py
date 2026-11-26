"""One-time Hugging Face login on this PC, typed by the OWNER (never by Claude): saves the owner's own Read token in
~/.cache/huggingface/token so Tools/trellis_client.py runs on the owner's free ZeroGPU quota instead of the tiny
anonymous one. The token is typed into a hidden prompt and never shown, logged or committed.

Run: "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/hf_login.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".pylibs_gradio"))
from huggingface_hub import get_token, login  # noqa: E402

print("Paste your Hugging Face READ token (huggingface.co/settings/tokens) and press Enter.")
print("The token stays hidden while you paste it. If asked 'Add token as git credential?', answer n.")
login(add_to_git_credential=False)
print("Saved on this PC:", bool(get_token()), "- you can close this tab.")
