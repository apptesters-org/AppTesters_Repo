from github import Github
import json
import argparse
import pandas as pd
from get_bundle_id import get_single_bundle_id
import os
import shutil
from datetime import timezone, timedelta

REPO_NAME = "apptesters-org/AppTesters_Repo"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--token", help="Github token")
    args = parser.parse_args()
    token = args.token

    out_file = "apps.json"
    clone_file = "index.html"

    with open(out_file, "r") as f:
        data = json.load(f)

    if os.path.isfile("bundleId.csv"):
        df = pd.read_csv("bundleId.csv")
    else:
        df = pd.DataFrame(columns=["name", "bundleId", "genre"])

    # clear apps
    data["apps"] = []

    g = Github(token)
    repo = g.get_repo(REPO_NAME)
    releases = repo.get_releases()

    for release in releases:
        for asset in release.get_assets():
            if (spl := asset.name.split("."))[-1] not in ("ipa", "dylib", "deb"):
                continue
            IS_IPA = spl[-1] == "ipa"
            name = ".".join(spl[:-1])
            # IST = UTC+5:30
            IST = timezone(timedelta(hours=5, minutes=30))
            created_at_ist = asset.created_at.astimezone(IST)
            date = created_at_ist.strftime("%Y-%m-%d")         # e.g., '2025-05-02'
            full_date = created_at_ist.strftime("%Y%m%d%H%M%S") # e.g., '20250502020230'
            try:
                app_name, version, tweaks = name.split("_", 2)
                tweaks, _ = tweaks.split("@", 1)
                if tweaks:
                    tweaks = f"Injected with {tweaks[:-1].replace("_", " ")}"
            except Exception:
                app_name = name
                version = "Unknown"
                tweaks = None

            if IS_IPA:
                if app_name in df.name.values:
                    info = {"bundle": df[df.name == app_name].bundleId.values[0], "genre": df[df.name == app_name].genre.values[0]}
                else:
                    info: dict = get_single_bundle_id(asset.browser_download_url)

                    if "error" in info:
                        print(f"[*] error detected in '{name}', deleting")
                        asset.delete_asset()
                        continue

                    df = pd.concat([df, pd.DataFrame(
                        {"name": [app_name], "bundleId": [info["bundle"]], "genre": [info["genre"]]})], ignore_index=True)

                data["apps"].append({
                    "name": app_name,
                    "type": int(info["genre"]),
                    "bundleID": str(info["bundle"]),
                    "bundleIdentifier": str(info["bundle"]),
                    "version": version,
                    "versionDate": date,
                    "fullDate": full_date,
                    "size": int(asset.size),
                    "down": asset.browser_download_url,
                    "downloadURL": asset.browser_download_url,
                    "developerName": "",
                    "localizedDescription": tweaks,
                    "icon": f"https://raw.githubusercontent.com/{REPO_NAME}/main/icons/{info["bundle"]}.png",
                    "iconURL": f"https://raw.githubusercontent.com/{REPO_NAME}/main/icons/{info["bundle"]}.png"
                })
            else:
                data["apps"].append({
                    "name": app_name,
                    "type": 5,  # type: dylib
                    "bundleId": f"org.apptesters.repo.{app_name.lower()}",
                    "bundleIdentifier": f"org.apptesters.repo.{app_name.lower()}",
                    "version": version,
                    "versionDate": date,
                    "fullDate": full_date,
                    "size": int(asset.size),
                    "down": asset.browser_download_url,
                    "downloadURL": asset.browser_download_url,
                    "developerName": "",
                    "localizedDescription": app_name,
                    "icon": "https://apptesters.org/apptesters-512x512.png",
                    "iconURL": "https://apptesters.org/apptesters-512x512.png"
                })

    data["apps"].sort(key=lambda x: x["fullDate"], reverse=True)
    df.to_csv("bundleId.csv", index=False)

    with open(out_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    shutil.copyfile(out_file, clone_file)
