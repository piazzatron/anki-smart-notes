## Milestones

- 1

  - [x] Auto fill mmemonic and example fields, for Japanese, with beginner examples, hardcoded everything

- 2

  - [x] Background thread OpenAI
  - [x] regenerate field button
  - [x] Config menu:

    - [x] Model selection
    - [x] mapping custom field names
    - [x] Placerolder isn't showing up for prompt box...
    - [x] validatate every prompt...
    - [x] Deleting prompts
    - [x] Adding prompts
    - [x] Editing prompts

  - [x] Per field regeneration
  - [ ] Add card flow will need something...
  - [x] Batch processing
    - [x] Need to be able to undo a batch... and undo in general?
  - [ ] Crash handling (what if openAI 500s, etc). Need to display some errors

  - [ ] Needs to have some sort of nice UI to indicate that a card has been updated in the background. Flash a border or something?
  - [ ] Need an icon for the options window and editor button (robot emoji?)
  - [ ] Decide on a name... AI Field Options kinda bland decent SEO tho
  - [x] Should have a way to test the prompts... oy

- BUGS
- [ ]Don't update on review if the fields are filled!!

- PRODUCT POLISH

  - [ ] Config menu looks like crap
  - [ ] Need some warnings around API rate limit when batching
  - [ ] Look up API tier to figure out batch limit
  - [ ] List out example fields when editing a card

- Distribution

  - [ ] Figure out what to vendor
  - [ ] license etc
  - ANKI Readme:
    - Inspired by intelliFiller, unmaintained etc
    - Should have example usage (For example sentences, mmemonics, etc)
    - Should link to GH
    - For feature requests/bugs, go to GH
    - if u like it give it a thumb so more ppl can find it
    - Note that it works in lowercase field names
    - Intelligently batch cards by your API tier
  - [ ] Make GH repo public
  - [ ] Supported anki versions

- DEV POLISH

  - [x] Python formatting
  - [ ] Mypy on save or smth?

  - [ ] std err
  - [ ] Debug logs
  - [ ] Pull out the one massive file elsewhere

- [ ] Beta Test with Evan

  - Is edit functionality discoverable?
  - Ask for feedback on documentation etc

- V2

  - Better batching support, esp for low tier API
  - Auto fill after losing focus on origin prompts

- LATER / V3

  - [ ] AI fields referencing other AI fields, generate in a particular order
  - [ ] Image creation support for mmemonics??
  - [ ] Project writeup, while it's fresh. Challenges, inspirations etc. Further notes in Obsidian

- NICE TO HAVE
  - [ ] Some build script
  - [ ] Contributing guidelines (lolz)

## Musings

- Should it fill the entire card, or a single field?
- It could automatically fill out chosen fields on edit AND on note review, if they're empty
- Each field could have an option to map to a prompt
