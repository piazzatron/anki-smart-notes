- [ ] Hotkey to generate
- [ ] Telemetry
- [x] What's new popup..

---

- [ ] Bug: deleting smart fields doesn't propagate to the dialog, so you get the smart field target error
- [ ] Per deck options (generate at review vs not)
- [ ] Prebaked prompts
- [ ] Investigate how to make this better w/o paying / OAuth?
- [ ] warning on batch
- [ ] Link to rate the addon
- [ ] Addon config should bring up GUI

- BUGS

- QoL

  - [ ] docs should link to GH at the top & the version
    - Should have my name somewhere i suppose...
    - kofi link?...
  - [ ] Need to pull in version somewhere
  - [ ] Need top lvl event handler for exceptions, which links to GH

- DEV POLISH

  - [ ] mypy on build
  - [ ] turn on mypy strict (it's rough...)

- Features

  - [ ] Pregenerated prompts for common use cases...
  - Better batching support, esp for low tier API
  - Edit entire deck
  - Auto fill after losing focus on origin prompts
  - AI fields referencing other AI fields, generate in a particular order
  - Image creation support for mmemonics??

- NICE TO HAVE
  - [ ] Contributing guidelines (lolz)
  - [ ] Could pre-empt the prompt with reply only with the answer.

## Beta test notes

- [x] Step 1: Install smart notes

- [x] Prompt Placeholder text was confusing. Need some sort of explanation about how to use the thing.
- [x] Would be nice to see all the fields in the add prompt menu
- [x] Need to double check that the prompt isn’t empty
- [ ] Auto generate doesn’t work on review time in mobile

- [x] Investigate batch processing work:

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
  - [x] Config menu:
  - [x] fix mypy running in loop lol
    - [x] Button for generate empty fields at edit time
    - [x] Wire up restore defaults button
  - [x] Crash handling (what if openAI 500s, etc). Need to display some errors
  - [x] Editor button should disable while things are happening
- [x] AI fields shouldn't be able to reference other AI fields
- [x] loading state can get stuck when testing if err
  - [x] prompt test doesn't take latest API key?
- [x] smart field can't target itself
- [x] Shouldn't be able to perform any AI ops on a card while one is in progress

  - [x] Manifest should include the anki plugin ID etc
  - [x] Batch popup should be nicer, tell u # succeeed and failed
  - [x] Periodic reminder to rate

- [x] remake the add prompt vid
- [x] Set min anki version

  - [x] Supported anki versions

- [x] license etc
- [x] GH releases, etc

- 6/5/24
- Should set up zip/distro & docs & then send it out
