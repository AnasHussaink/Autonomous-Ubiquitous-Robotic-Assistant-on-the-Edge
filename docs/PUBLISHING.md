# Publish this documentation on GitHub

This documentation package contains `README.md` and `docs/`. Copy both into the root of the existing AURA repository. It supplements the project; it is not a standalone application download.

## Option 1: GitHub website

1. Open your repository: https://github.com/AnasHussaink/Autonomous-Ubiquitous-Robotic-Assistant-on-the-Edge
2. Extract `AURA-GitHub-README.zip` on your laptop.
3. At the repository root, select **Add file > Upload files**.
4. Drag in `README.md` and the complete `docs` folder. Preserve the folder structure; uploading only the README will break its images.
5. Review the file list. It should contain documentation, image assets, and reference setup files only.
6. Commit with a message such as `docs: add complete AURA hardware and software guide`.
7. Open the repository homepage and check that all images render.

If the web uploader does not replace the existing README, open `README.md`, select the edit button, paste the new Markdown, and commit it. Upload `docs/` with its folder structure separately.

## Option 2: Git on the Raspberry Pi

Copy the package contents into the existing project folder, replacing its README and adding `docs/`. Then run:

```bash
cd ~/Desktop/Pi-Edge-Smart-Display
git status
git diff -- README.md
git add README.md docs
git diff --cached --stat
git commit -m "docs: add complete AURA hardware and software guide"
git push
```

Inspect existing staged changes before committing: a Git commit includes all staged files, even if they were staged before these commands. Do not publish the private troubleshooting PDF, extracted conversation text, or local review screenshots. They are not included in this package.

## Documentation checks already performed

- Matched the guide to the supplied source-code snapshot.
- Applied the owner's confirmation: Raspberry Pi 4, INMP441 microphone, MAX98357A amplifier/speaker, no camera or Coral TPU in the completed build.
- Rendered the dashboard images from the supplied HTML with explicit sample state/data.
- Used relative GitHub image paths and included their assets.
- Preserved the existing software license and credited the enclosure sources.

The reference setup files are newly prepared documentation examples. They have not been tested on the owner's physical Pi. They do not replace application code or the original `start_aura.sh` automatically.
