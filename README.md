# Decoding the Zodiac's Z32 Cipher: A Computational Solution and Satellite Discovery

## The Cipher

In June 1970, the Zodiac Killer mailed a cipher to the San Francisco Chronicle alongside a Phillips 66 road map of the Bay Area. The 32-character cipher—now known as Z32—was accompanied by a cryptic hint:

> "The Map coupled with this code will tell you where the bomb is set. You have until next Fall to dig it up."

On the map, the Zodiac had drawn a compass rose centered on Mount Diablo, with the annotation: **"is to be set to Mag. N."** In the same letter, he provided another clue: the location could be found by measuring **"radians & # inches along the radians"** from the center point.

For over 50 years, this cipher has remained unsolved.

## The Approach

This project takes the Zodiac's hints literally. If the cipher encodes a location as "radians and inches along the radians," then the plaintext must be a phrase describing:

1. A **distance** in inches (to be measured on the map)
2. A **direction** expressed in clock positions (the "radians")

The Phillips 66 map has a scale of approximately **1 inch = 6.4 miles**. The Zodiac's compass rose suggests directions should be read as clock positions (12 o'clock = North, 3 o'clock = East, etc.), converted to magnetic bearing and then to true bearing using the ~17° east magnetic declination of the Bay Area in 1970.

### Constraint-Based Filtering

The Z32 cipher uses a substitution system where repeated symbols in the ciphertext must map to the same plaintext letter. Analysis of the original cipher reveals three critical constraints:

- Position 0 and position 25 share the same symbol
- Position 1 and position 31 share the same symbol  
- Position 5 and position 13 share the same symbol

Any valid solution must satisfy all three constraints.

### The Search Space

The solver generates all phrases matching the pattern:

```
{prefix} {number} {fraction} {radian_word} {angle}
```

Where:
- **prefix**: "A", "AT", "BY", "IN", "TO" (or blank)
- **number**: "ONE" through "TWELVE" (or blank)
- **fraction**: Common fractions ("HALF", "QUARTER", "THREE EIGHTHS", etc.) or blank
- **radian_word**: "RADIAN", "RADIANS", "OCLOCK"
- **angle**: "ONE" through "TWELVE"

This generates **6,554 candidate phrases**. After applying the three cipher constraints, only **13 candidates remain**.

## The Results

All 13 surviving candidates share remarkable properties:

| Property | Value |
|----------|-------|
| First word | IN |
| Last word | TEN |
| Clock direction | 10 o'clock (300° magnetic → 317° true) |
| General area | Northwest of Mount Diablo |

The candidates differ only in the distance component. Sorting by proximity to known Zodiac crime scenes, the top candidate is:

### **"IN THREE AND THREE EIGHTHS RADIANS TEN"**

**Constraint verification:**
- Position 0 (I) = Position 25 (I) ✓
- Position 1 (N) = Position 31 (N) ✓
- Position 5 (E) = Position 13 (E) ✓

**Decoded location:**
- Distance: 3.375 inches × 6.4 mi/in = **21.6 miles**
- Direction: 10 o'clock = 300° magnetic = **317° true**
- Coordinates: **38.109952°N, 122.185349°W**

## Geographic Significance

The decoded coordinates place the location in the hills northwest of Vallejo, California—directly between the Zodiac's first two confirmed crime scenes.

![Bay Area map showing Zodiac crime scenes and Z32 solution](https://i.imgur.com/TAGCE6U.jpeg)
*Map showing confirmed Zodiac crime scenes (blue pins) and the Z32 decoded coordinate (orange pin near Vallejo). Mount Diablo, the cipher's reference point, is marked with the red pin to the south.*

| Location | Distance from Z32 Point |
|----------|------------------------|
| Lake Herman Road (Dec 20, 1968) | 2.47 miles |
| Blue Rock Springs (Jul 4, 1969) | 1.87 miles |
| Tony Borges Ranch | **1.00 mile** |

### The Borges Ranch Connection

The Tony Borges Ranch is where **Stella Borges** lived—the woman who discovered the bodies of Betty Lou Jensen and David Faraday on the night of December 20, 1968. She was driving from her ranch when her headlights illuminated the crime scene.

But there's more. According to Robert Graysmith's *Zodiac Unmasked* and interviews with Borges family members, Stella Borges reported seeing a strange man repeatedly in the months before the murder:

> "The big man swam in the cold water and stood like an apparition at her gate."

Her nephew Albert Losado confirmed:

> "She would tell us that she would see this guy driving up and down the road... I guess a few times he stopped and stared at her. Gave her the chills."

**The Zodiac was stalking this exact area before he committed his first murder.** If the Z32 cipher is correctly decoded, it points back to his hunting ground.

## The Satellite Discovery

Previous researchers who arrived at similar plaintext solutions noted only that the coordinates were "near Lake Herman Road." None examined satellite imagery of the location.

When we did, we found something remarkable.

![Satellite view showing Z32 coordinates and triangle](https://i.imgur.com/BE45myB.jpeg)
*Satellite imagery of the Z32 decoded location (38.109952, -122.185349). The red pin marks the calculated coordinates. Note the distinct green triangular shape visible to the northwest—this is the anomaly described below.*

### A Triangular Anomaly

At coordinates **38.111128°N, 122.187803°W**—approximately 800 feet from the calculated Z32 point—satellite imagery reveals a distinct **triangular vegetation pattern**:

![Close-up of the triangular vegetation anomaly](https://i.imgur.com/vFA5fHt.jpeg)
*Close-up satellite view of the triangular anomaly at 38.111128, -122.187803. The shape measures approximately 100 feet per side, with sharp geometric edges. The vibrant green vegetation stands in stark contrast to the surrounding brown, barren terrain.*

- Approximately **100 feet per side**
- Sharp, geometric edges inconsistent with natural growth
- Vibrant green vegetation in otherwise brown, barren terrain
- Located on undeveloped land between the Borges Ranch properties
- NOTE:  Z32 Cipher contains two triangle symbols (hollow and filled).

### Historical Imagery Analysis

Using historical aerial photography from [historicaerials.com](https://www.historicaerials.com):

| Year | Triangle Visible? |
|------|-------------------|
| 1964 | **NO** |
| 1968 | **YES** |
| 1970s–present | YES |

**The triangle appears between 1964 and 1968**—precisely the window when the Zodiac began his documented stalking of the Lake Herman Road area and committed his first murders.

### The Fertilizer Hypothesis

In his November 9, 1969 letter to the San Francisco Chronicle, the Zodiac described his bomb design in detail:

> "The system checks out from one end to the other in my tests. What you do not know is whether the death machine is at the sight or whether it is being stored in my basement for future use... **one bag of ammonium nitrate fertilizer** & 1 gallon of stove oil..."

Ammonium nitrate is a nitrogen-rich compound (34% N) commonly used as agricultural fertilizer. When concentrated in soil, it produces **sustained, localized vegetation growth** that persists for decades.

The surrounding area has a history of mercury mining (Hastings Mine, St. John's Mine), which left soils contaminated with heavy metals that typically **inhibit** plant growth. A patch of vigorous green vegetation in this environment would require an external nitrogen source.

**If the Zodiac buried bags of ammonium nitrate at this location—whether as a functional device or a decoy—the result after 50+ years would be exactly what we observe: a geometric patch of thriving vegetation in otherwise barren terrain.**

## Precision and Error Analysis

The triangle's location (38.111128°N, 122.187803°W) is approximately 800 feet from the calculated Z32 coordinates (38.109952°N, 122.185349°W). This offset is well within expected error margins:

| Error Source | Estimated Impact |
|--------------|------------------|
| Pencil width on folded map | ±1/16" = ±0.4 miles |
| Magnetic declination uncertainty | ±1° = ±0.3 miles at 21.6 mi |
| Map fold distortion | Unknown |
| Measurement precision | ±0.125" = ±0.8 miles |

**Combined expected error: ~0.5–1.0 miles**

The triangle falls comfortably within this range. If the Zodiac intended for someone to find a physical landmark, the triangle would be visible to anyone who got "close enough" by following the cipher.

## Prior Work

This plaintext solution—"IN THREE AND THREE EIGHTHS RADIANS TEN"—has been proposed independently by other researchers. The computational approach described here arrived at the same candidate through systematic constraint satisfaction.

**However, no prior researcher examined satellite imagery of the decoded location or identified the triangular vegetation anomaly.**

The novel contribution of this project is:
1. Reproducible, constraint-based methodology
2. Satellite imagery analysis revealing a geometric landmark
3. Historical aerial photography showing the triangle's appearance between 1964–1968
4. Connection to the Zodiac's documented fertilizer bomb design

## The Coincidences

Consider what would need to be true for this to be pure chance:

1. A phrase that satisfies all three cipher constraints
2. Points to a location between the Zodiac's first two crime scenes
3. Within 1 mile of the ranch he was documented stalking before the murders
4. Contains a geometric vegetation anomaly visible from satellite imagery
5. That anomaly first appears in aerial photography between 1964–1968
6. The anomaly's characteristics are consistent with nitrogen-enriched soil
7. The Zodiac explicitly mentioned burying ammonium nitrate fertilizer

Each coincidence alone might be dismissed. Together, they form a pattern that warrants investigation.

## Running the Code

```bash
python z32.py
```

The solver outputs all candidates that pass the cipher constraints, sorted by proximity to known Zodiac crime scenes. The top results cluster in the hills northwest of Vallejo, all pointing to the 10 o'clock direction from Mount Diablo.

## What This Means

This analysis does not prove the Zodiac buried anything at this location. A 32-character cipher provides insufficient constraints to guarantee any solution is correct.

What it demonstrates is:

1. **A systematic methodology** produces a small set of candidates (13 out of 6,554)
2. **All candidates converge** on the same general area and direction
3. **The top candidate** places the location in an area with documented Zodiac activity
4. **Satellite imagery reveals** an anomaly consistent with the Zodiac's stated methods
5. **Historical photography confirms** the anomaly appeared during the relevant time period

Whether this justifies ground investigation is a question for law enforcement and researchers with appropriate expertise and authority.

---

*This project is released for research and educational purposes. The author makes no claims of definitive solution and encourages independent verification of all findings.*