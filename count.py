import pandas as pd

keys = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "←", 
    "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", 
    "A", "S", "D", "F", "G", "H", "J", "K", "L", "↵", 
    "⇧", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", 
    " "
]

texts = [
    "⇧A ZEBRA, 2 MICE, 5 DOGS JUMPED.↵",
    "3 KIND CATS, 6 FROGS, 9 FISH SWIM.↵",
    "⇧QUIETLY, 8 ELEPHANTS WALK BY 4 TREES.↵",
    "⇧VEXING BUGS ON 1 LEAF, 0 HARM DONE.↵",
    "7 HENS LAY GOLDEN EGGS, X MARKS SPOT.↵",
    "⇧WHY DID UPTON, THE 1ST, BUY 9←8 PLUMS⇧/↵",
]

# Concatenate all texts
all_texts = "".join(texts)

# Count frequency of each key
freq_dict = {key: all_texts.count(key) for key in keys}

# Convert to DataFrame
df = pd.DataFrame.from_dict(freq_dict, orient='index', columns=['Frequency'])

# Save to csv
df.to_csv('key_frequency.csv')
