## Milestones

- 2

  - [ ] Set min anki version
  - [x] Config menu:

    - [ ] Button for generate empty fields at edit time
    - [ ] Link to rate the addon
    - [ ] Wire up restore defaults button

  - [ ] Crash handling (what if openAI 500s, etc). Need to display some errors
  - [ ] Addon config should bring up GUI

  - [ ] Editor button should disable while things are happening

- BUGS
- [ ] AI fields shouldn't be able to reference other AI fields
- [ ] smart field can't target itself
- [ ] Shouldn't be able to perform any AI ops on a card while one is in progress

- PRODUCT POLISH

  - [ ] Need top lvl event handler for exceptions, which links to GH
  - [ ] Need some warnings around API rate limit when batching
  - [ ] Batch popup should be nicer, tell u # succeeed and failed
  - [ ] Need to pull in version somewhere
  - [ ] Periodic reminder to rate

- Distribution

  - [ ] GH releases, etc
  - [ ] license etc
  - [ ] Fewer logs...
  - ANKI Readme:
    - Inspired by intelliFiller, unmaintained etc
    - Should have example usage (For example sentences, mmemonics, etc)
    - Should link to GH
    - For feature requests/bugs, go to GH
    - if u like it give it a thumb so more ppl can find it
    - Note that it works in lowercase field names
    - Intelligently batch cards by your API tier
  - [ ] Supported anki versions

- DEV POLISH

  - [ ] mypy on build
  - [ ] turn on mypy strict (it's rough...)
  - [ ] std err
  - [ ] Debug logs

- [ ] Beta Test with Evan

  - Is edit functionality discoverable?
  - Ask for feedback on documentation etc

- V2

  - Better batching support, esp for low tier API
  - Edit entire deck
  - Auto fill after losing focus on origin prompts

- LATER / V3

  - [ ] AI fields referencing other AI fields, generate in a particular order
  - [ ] Image creation support for mmemonics??
  - [ ] Project writeup, while it's fresh. Challenges, inspirations etc. Further notes in Obsidian

- NICE TO HAVE
  - [ ] Contributing guidelines (lolz)

## Musings

- Should it fill the entire card, or a single field?
- It could automatically fill out chosen fields on edit AND on note review, if they're empty
- Each field could have an option to map to a prompt

## DONE

- 1
  - [x] Auto fill mmemonic and example fields, for Japanese, with beginner examples, hardcoded everything
- 2

  - [x] Refactor: Pull out the one massive file elsewhere

- [x] Some build script
- [x] Python formatting
- [x] Make GH repo public
- [x] Setuptools distribution stuff... (just zip for now)
  - [x] Emoji in the title?
- [x] Figure out what to vendor
- [x] Look up API tier to figure out batch limit
- [x] List out example fields when editing a card
- [x] Don't update on review if the fields are filled!!
- [x] Config menu looks like crap
- [x] On first run, does it not work? What was that 'choices' thing it echoed?
- [x] Should have a way to test the prompts... oy
- [x] Need an icon for the options window and editor button (robot emoji?)
- [x] Decide on a name... AI Field Options kinda bland decent SEO tho
- [x] Needs to have some sort of nice UI to indicate that a card has been updated in the background. Flash a border or something?
- [x] Get to 0 mypy errors so it's useful
- [x] Per field regeneration
- [x] Add card flow will need something... v buggy
- [x] Batch processing
  - [x] Need to be able to undo a batch... and undo in general?
- [x] Switch model button should have some text about the batch limitations, and link to rate limits.
- [x] Link to get OpenAI token
- [x] Model selection
- [x] mapping custom field names
- [x] Placerolder isn't showing up for prompt box...
- [x] validatate every prompt...
- [x] Deleting prompts
- [x] Adding prompts
- [x] Editing prompts
- [x] Background thread OpenAI
- [x] regenerate field button

- 6/5/24
- Should set up zip/distro & docs & then send it out
