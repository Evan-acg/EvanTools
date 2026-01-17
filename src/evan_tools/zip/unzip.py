from pathlib import Path


def unzip_7z(file_path: Path, output: Path, *, password: str | None = None) -> bool:
    import py7zr

    try:
        pwd = password if password else None
        
        suffix = file_path.suffix
        if suffix and suffix[1:].isdigit():
            import multivolumefile
            volume_num = int(suffix[1:])
            base_name = file_path.parent / file_path.stem
            with multivolumefile.open(base_name, mode='rb', volume=volume_num) as target_archive:
                with py7zr.SevenZipFile(target_archive, 'r', password=pwd) as archive:  # type: ignore[arg-type]
                    archive.extractall(path=output)
            return True
        else:
            with py7zr.SevenZipFile(file_path, mode="r", password=pwd) as z:
                z.extractall(path=output)
            return True
    except Exception as e:
        print(f"Error unzipping 7z file: {e}")
        return False
