def parse_name(full_name: str) -> dict[str, str]:
    parts = full_name.strip().split()

    if not parts:
        return {
            "full_name": "",
            "first_name": "",
            "middle_name": "",
            "last_name": "",
        }

    if len(parts) == 1:
        return {
            "full_name": parts[0],
            "first_name": parts[0],
            "middle_name": "",
            "last_name": "",
        }

    if len(parts) == 2:
        return {
            "full_name": " ".join(parts),
            "first_name": parts[0],
            "middle_name": "",
            "last_name": parts[1],
        }

    return {
        "full_name": " ".join(parts),
        "first_name": parts[0],
        "middle_name": " ".join(parts[1:-1]),
        "last_name": parts[-1],
    }


import re


import re


INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Delhi",
]


def parse_address(address: str) -> dict[str, str]:

    if not address:
        return {
            "full_address": "",
            "house_number": "",
            "street": "",
            "locality": "",
            "city": "",
            "state": "",
            "pincode": "",
        }

    full_address = " ".join(address.strip().split())

    working = full_address

    # -----------------------------------------
    # 1. PINCODE
    # -----------------------------------------

    pincode_match = re.search(
        r"\b[1-9][0-9]{5}\b",
        working
    )

    pincode = (
        pincode_match.group()
        if pincode_match
        else ""
    )

    if pincode_match:
        working = (
            working[:pincode_match.start()]
            + working[pincode_match.end():]
        )

    # -----------------------------------------
    # 2. STATE
    # -----------------------------------------

    state = ""

    for candidate in sorted(
        INDIAN_STATES,
        key=len,
        reverse=True
    ):

        match = re.search(
            rf"\b{re.escape(candidate)}\b",
            working,
            re.IGNORECASE
        )

        if match:
            state = match.group()

            working = (
                working[:match.start()]
                + working[match.end():]
            )

            break

    working = " ".join(working.split())

    # -----------------------------------------
    # 3. HOUSE NUMBER
    # -----------------------------------------

    house_number = ""

    house_match = re.match(
        r"^#?([0-9]+[A-Za-z]?(?:[-/][0-9A-Za-z]+)?)\b",
        working
    )

    if house_match:

        house_number = house_match.group(1)

        working = working[
            house_match.end():
        ].strip()

    # -----------------------------------------
    # 4. STREET
    # -----------------------------------------

    street_match = re.search(
        r"\b"
        r"(?:\d+(?:st|nd|rd|th)\s+)?"
        r"(?:\w+\s+)*"
        r"(?:Main\s+)?"
        r"(?:Road|Rd|Street|St|Cross|"
        r"Lane|Ln|Avenue|Ave|Highway|Hwy)"
        r"\b",
        working,
        re.IGNORECASE,
    )

    street = ""

    if street_match:

        street = street_match.group().strip()

        working = (
            working[:street_match.start()]
            + working[street_match.end():]
        )

    working = " ".join(working.split())

    # -----------------------------------------
    # 5. CITY
    # -----------------------------------------

    # For your current address format, the city
    # is the final geographic component before
    # the state.

    known_cities = [
        "Bangalore",
        "Bengaluru",
        "Mysore",
        "Mysuru",
        "Hosur",
        "Chennai",
        "Mumbai",
        "Delhi",
        "Hyderabad",
        "Pune",
        "Kolkata",
        "Coimbatore",
    ]

    city = ""

    for candidate in sorted(
        known_cities,
        key=len,
        reverse=True
    ):

        match = re.search(
            rf"\b{re.escape(candidate)}\b",
            working,
            re.IGNORECASE
        )

        if match:
            city = match.group()
            working = (
                working[:match.start()]
                + working[match.end():]
            )
            break

    # -----------------------------------------
    # 6. REMAINING TEXT → LOCALITY
    # -----------------------------------------

    locality = " ".join(working.split())

    return {
        "full_address": full_address,
        "house_number": house_number,
        "street": street,
        "locality": locality,
        "city": city,
        "state": state,
        "pincode": pincode,
    }

if __name__=="__main__":
    res=parse_name("Abhiram Raghunand")
    print(res)
    address="#3 SWWC 407 SFS 4th phase Yelahanka new town Bangalore Karnataka 560064"
    res1=parse_address(address=address)
    print(res1)
