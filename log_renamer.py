import os
import sys
import re
from tinytag import TinyTag

VALID_FILE_TYPES = {
    ".log",
    ".cue",
    ".accurip"
}

IGNORED_FILE_NAMES = {
    "info",
    "lineage"
}

def GetFiles() -> list[str]:
    files = []
    directory = sys.argv[1]

    for dirPath, _, fileNames in os.walk(directory):
        for fileName in fileNames:
            _, fileType = os.path.splitext(fileName)

            # Ignore logs from analog rips.
            if fileName.lower() in IGNORED_FILE_NAMES:
                continue

            if fileType not in VALID_FILE_TYPES:
                continue

            filePath = os.path.join(dirPath, fileName)
            files.append(filePath)

    return files

# real codecs, other ones are mental illnesses
AUDIO_TYPES = {
    ".mp3",
    ".ogg",
    ".flac",
    ".aac"
}

def GetAudio(folder: str) -> str | None:
    if not os.path.isdir(folder):
        folder = os.path.dirname(folder)

    for file in os.listdir(folder):
        _, fileType = os.path.splitext(file)

        if fileType not in AUDIO_TYPES:
            continue

        return os.path.join(folder, file)

def HasMultipleDiscs(filePath: str, tag: TinyTag | None) -> bool:
    song = GetAudio(filePath)
    tag = tag or TinyTag.get(song)

    return tag.disc_total and tag.disc_total != 1

class DiscNumberNotFoundError(Exception):
    """Raised if a disc number is not found from a log file."""

def GetDiscNumber(filePath: str) -> int:
    path, _ = os.path.splitext(filePath)
    file = os.path.basename(path)

    # Find the first sequence of numbers in the string, but search backwards.
    match = re.search(r'\d+', file[::-1])

    if match:
        # Extract the number as a string, and undo the reverse.
        number = match.group()[::-1]

        return number
    else:
        # No number found, return 1 which will cause the script to halt.
        # This way, the user is at least alerted to their files lacking a valid number.
        raise DiscNumberNotFoundError

translations = str.maketrans({
    "<": "﹤",
    ">": "﹥",
    ":": "ː",
    '"': "“",
    "\\": "∖",
    "/": "⁄",
    "|": "⼁",
    "?": "﹖",
    "*": "﹡"
})

def GetRenameString(filePath: str) -> str:
    song = GetAudio(filePath)
    tag = TinyTag.get(song)
    newName = tag.album.translate(translations)

    # WORKAROUND: Hidden track (pre-gap) logs.
    if "HTOA" in filePath or "Hidden Track" in filePath:
        return f"{newName} (HTOA)"

    # Our release has multiple discs? We need a specially formatted name.
    # This assumes the files (logs/cues) include the disc number somewhere in their filename already.
        # eg: 2Pac - All Eyez on Me (CD1).cue
    if HasMultipleDiscs(filePath, tag):
        return f"{newName} (Disc {GetDiscNumber(filePath)})"

    return newName

def RenameFile(filePath: str) -> bool:
    try:
        newName = GetRenameString(filePath)
    except DiscNumberNotFoundError:
        print(f"Failed to find disc number for '{filePath}', skipping log...")

        return False

    _, fileType = os.path.splitext(filePath)
    renamePath = os.path.join(os.path.dirname(filePath), newName + fileType)

    if filePath == renamePath:
        return False

    os.rename(filePath, renamePath)

    print(f"{os.path.basename(filePath)} renamed to {newName + fileType}")

    return True

def DoRenames():
    files = GetFiles()

    if not files:
        print("No files found.")

        return
    
    renameCount = 0
    
    for filePath in files:
        successful = RenameFile(filePath)

        if not successful:
            continue

        renameCount += 1

    print(f"Done, renamed {renameCount} files!")

if __name__ == "__main__":
    if not sys.argv[0]:
        print("No directory provided, wtf are you doing")
        sys.exit()

    DoRenames()