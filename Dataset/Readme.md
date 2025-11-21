Here we put some dataset for our AI Agent project. They have different formats.


## Writing systems and transliteration

This repository ultimately works with **Sanskrit text**, which can appear in several different writing systems or transliteration schemes. In practice you will most often see:

- **Devanagari** (e.g. देवनागरी) – the standard Indic script for Sanskrit
- **IAST** – a human-readable Latin transliteration with diacritics (ā, ī, ṛ, ś, ṣ, …)
- **SLP1** – a machine-friendly Latin transliteration using only ASCII characters

Understanding the differences between these three is useful when consuming DCS data or integrating it with other Sanskrit resources (dictionaries, corpora, etc.).

### Devanagari

**Devanagari** is the original script used in most printed Sanskrit texts today.  
Example:

> देवनागरी लिपिः संस्कृतभाषायाः प्राच्यः लेखनपद्धतिः अस्ति ।

Devanagari is excellent for **human reading**, but inconvenient for many NLP tasks:

- it uses a large Unicode range and complex rendering (ligatures, combining marks),
- some tools expect Latin input,
- and many legacy resources (e.g. dictionaries, corpora) are stored in Latin transliteration.

For this reason, it is common to convert Devanagari into a Latin scheme such as IAST or SLP1 before processing.

### IAST (International Alphabet of Sanskrit Transliteration)

**IAST** is a scholarly transliteration system that represents Sanskrit sounds with Latin letters plus diacritics:

- long vowels: ā, ī, ū  
- retroflex consonants: ṭ, ḍ, ṇ  
- special sibilants: ś, ṣ  
- vocalic r/l: ṛ, ṝ, ḷ, ḹ  
- nasal and visarga: ṃ, ḥ

Example (same sentence as above):

> devanāgarī lipiḥ saṃskṛtabhāṣāyāḥ prācyaḥ lekhanapaddhatiḥ asti ।

IAST is **very readable** and is the standard in academic publications. However:

- it requires Unicode combining characters,
- and some tooling (regexes, older code) is easier to write if everything is plain ASCII.

For this reason, IAST is ideal for **display and human consumption**, but not always the most convenient internal format.

### SLP1 (Sanskrit Library Phonetic basic)

**SLP1** is a transliteration scheme designed to be:

- **1:1 with Sanskrit phonology**, and
- **pure ASCII**, i.e., only the characters `a–z`, `A–Z`, and a few symbols.

It encodes all the distinctions of IAST (long vs. short vowels, retroflex vs. dental, etc.) using:

- **capital letters** for long vowels (A, I, U, …),
- **specific letters** for special consonants (`w, W, q, Q, R, Y, N, S, z`, etc.),
- `M` for anusvāra (ṃ) and `H` for visarga (ḥ).

Example (same sentence again):

> devanaAgarii lipiH saMskftabhASAyAH prAcyaH lekhanapaddhatiH asti ।

(Exact spelling may vary slightly depending on the SLP1 implementation.)

SLP1 is especially convenient because:

- it is easy to handle with simple tools (no diacritics, no combining marks),
- many digital resources (e.g. Monier-Williams lexicon, some corpora) use SLP1 or a closely related scheme internally,
- conversions between **Devanagari ↔ IAST ↔ SLP1** are algorithmic and reversible (assuming standard spelling).

In this repository, you may encounter SLP1 when integrating DCS data with external lexicons or when building automated processing pipelines.

### Quick comparison table

The table below shows a **small subset** of common Sanskrit sounds in the three systems.  
It is not exhaustive, but illustrates the general pattern.

| Sound value            | Devanagari | IAST | SLP1 |
|------------------------|-----------:|:-----|:-----|
| short a                | अ          | a    | a    |
| long ā                 | आ          | ā    | A    |
| short i                | इ          | i    | i    |
| long ī                 | ई          | ī    | I    |
| short u                | उ          | u    | u    |
| long ū                 | ऊ          | ū    | U    |
| vocalic ṛ              | ऋ          | ṛ    | f    |
| vocalic ṝ              | ॠ          | ṝ    | F    |
| vocalic ḷ              | ऌ          | ḷ    | x    |
| vocalic ḹ              | ॡ          | ḹ    | X    |
| e                      | ए          | e    | e    |
| o                      | ओ          | o    | o    |
| ai                     | ऐ          | ai   | E    |
| au                     | औ          | au   | O    |
| ka                     | क          | ka   | ka   |
| kha                    | ख          | kha  | Ka   |
| ga                     | ग          | ga   | ga   |
| gha                    | घ          | gha  | Ga   |
| ṅa                     | ङ          | ṅa   | Na   |
| ca                     | च          | ca   | ca   |
| cha                    | छ          | cha  | Ca   |
| ja                     | ज          | ja   | ja   |
| jha                    | झ          | jha  | Ja   |
| ña                     | ञ          | ña   | Ya   |
| ṭa                     | ट          | ṭa   | wa   |
| ṭha                    | ठ          | ṭha  | Wa   |
| ḍa                     | ड          | ḍa   | qa   |
| ḍha                    | ढ          | ḍha  | Qa   |
| ṇa                     | ण          | ṇa   | Ra   |
| ta (dental)            | त          | ta   | ta   |
| tha (dental)           | थ          | tha  | Ta   |
| da (dental)            | द          | da   | da   |
| dha (dental)           | ध          | dha  | Da   |
| na (dental)            | न          | na   | na   |
| pa                     | प          | pa   | pa   |
| pha                    | फ          | pha  | Pa   |
| ba                     | ब          | ba   | ba   |
| bha                    | भ          | bha  | Ba   |
| ma                     | म          | ma   | ma   |
| ya                     | य          | ya   | ya   |
| ra                     | र          | ra   | ra   |
| la                     | ल          | la   | la   |
| va                     | व          | va   | va   |
| śa                     | श          | śa   | Sa   |
| ṣa                     | ष          | ṣa   | za   |
| sa                     | स          | sa   | sa   |
| ha                     | ह          | ha   | ha   |
| anusvāra               | ं          | ṃ    | M    |
| visarga                | ः          | ḥ    | H    |

In code, you can use existing libraries (e.g. `indic_transliteration.sanscript`) to convert between these systems instead of implementing the mappings by hand.
