def get_frame_ranges(frame_ids):
    """
    Convert a list/array of frame IDs into range strings.
    Example: [0,1,2,3,4,5,8,9,10] -> "0-5, 8-10"
    """
    if len(frame_ids) == 0:
        return "None"

    # Sort the unique frame IDs
    frames = sorted(set(frame_ids))

    ranges = []
    start = frames[0]
    end = frames[0]

    for i in range(1, len(frames)):
        # If current frame is consecutive, extend the range
        if frames[i] == end + 1:
            end = frames[i]
        else:
            # Add the completed range
            if start == end:
                ranges.append(f"{start}")
            else:
                ranges.append(f"{start}-{end}")
            # Start new range
            start = frames[i]
            end = frames[i]

    # Add the last range
    if start == end:
        ranges.append(f"{start}")
    else:
        ranges.append(f"{start}-{end}")

    return ", ".join(ranges)
