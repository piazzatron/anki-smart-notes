## Milestones

- 1

  - [x] Auto fill mmemonic and example fields, for Japanese, with beginner examples, hardcoded everything

- 2

  - [x] Background thread OpenAI
  - [ ] regenerate field button
  - [ ] Config menu:
    - [x] Model selection
    - [x] mapping custom field names
    - [ ] validatate every prompt...
    - [ ] UI polish, this table looks bad
    - [ ] Deleting prompts
    - [ ] Adding prompts
  - [ ] Add card flow will need something...
  - [ ] Batch processing
  - [ ] Crash handling (what if openAI 500s, etc). Need to display some errors

  - [ ] Needs to have some sort of nice UI to indicate that a card has been updated in the background. Flash a border or something?
  - [ ] Need an icon for the options window and editor button (robot emoji?)
  - [ ] Decide on a name... AI Field Options kinda bland decent SEO tho
  - [ ] Should use QSpinbox...

- Distribution

  - [ ] license etc
  - ANKI Readme:
    - Inspired by intelliFiller, unmaintained etc
    - Should have example usage (For example sentences, mmemonics, etc)
    - Should link to GH
    - For feature requests/bugs, go to GH
    - if u like it give it a thumb so more ppl can find it
    - Note that it works in lowercase field names
  - [ ] Make GH repo public
  - [ ] Supported anki versions

- DEV POLISH

  - [ ] Python linting/formatting etc
  - [ ] std err
  - [ ] Debug logs

- [ ] Beta Test with Evan

  - Ask for feedback on documentation etc

- LATER

  - [ ] Image creation support for mmemonics??

- NICE TO HAVE
  - [ ] Some build script
  - [ ] Contributing guidelines (lolz)

## Musings

- Should it fill the entire card, or a single field?
- It could automatically fill out chosen fields on edit AND on note review, if they're empty
- Each field could have an option to map to a prompt
