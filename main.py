from pathlib import Path


from src.evan_tools import gather_paths


def main():
    path: Path = Path(r"C:\Users\Evan\Desktop\skills")
    for p in gather_paths([path], deep=True):
        print(p)


if __name__ == "__main__":
    main()
