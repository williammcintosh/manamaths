# Mana Maths — Project Vision

This project is not just a static website or a pile of PDFs.

The long-term goal is to build a **teacher-facing lesson planning system** where a teacher can chat with a language model and say things like:

> "I need a lesson on place value."
> "My students are struggling, add more simple entry-level problems."
> "We already covered the basics, remove the easy stuff and give me harder questions."
> "Make this OneNote-friendly."
> "Turn this into something I can project."
> "Give me a printable PDF."

The model should use the learning objective database as its source of truth.

## Current priority

Keep building both the website and the PDFs, but they need **different jobs**.

- **The website** is the preview and editing layer.
- **The PDFs** are the final classroom export.

Do not treat the website as a PDF viewer. Embedded PDF iframes are clunky and should not be the main experience.

The website should show teachers what is inside each learning objective in a clean HTML/CSS format:
- learning objective title
- short teacher summary
- key vocabulary
- prerequisite knowledge
- teaching notes
- module cards
- Start / Build / Push module cards
- links or buttons to export/download PDFs
- eventually options for Google Slides, Google Classroom, and OneNote

The PDFs should remain the polished classroom artefacts:
- printable
- projectable
- clean layout
- useful for OneNote import
- useful for whiteboard projection
- useful for students working directly from the board

## Important architecture idea

The learning objective content should be structured as **reusable modules**, not hard-coded as one flat page.

Each LO should eventually be stored in a structured format, likely JSON or similar, with fields like:
- objective title
- year level
- topic
- difficulty tier
- module type
- teacher notes
- student notes
- worked examples
- practice questions
- extension questions
- answers
- tags
- prerequisites
- export options

Then the same source content can generate:
1. the website preview
2. the PDF
3. a future editable lesson plan
4. a slide deck
5. a OneNote-friendly layout

## Main design principle

**Single source of truth.**

Do not duplicate content separately for website and PDF if avoidable. The same LO/module data should drive both.

## Future chatbot workflow

Teacher chats with the bot.
Bot searches the LO/module database.
Bot assembles a lesson plan.
Teacher previews it on the website.
Teacher asks for edits.
Bot modifies the module selection or difficulty mix.
Teacher exports the final version as PDF, Slides, or OneNote-friendly content.

Example future commands:
- remove Start Tasks (foundation) questions
- add more entry-level decimal place value questions
- make this shorter
- make this a 20-minute starter
- make this a full-period lesson
- add spicy challenge problems
- remove notes and show only questions
- include worked answers
- make a projected version
- make a printable version

## What this means for current development

When working on the LO pages, do not overfocus on making the website act like the final teaching document.

- The website should be clean, modular, readable, and useful for previewing.
- The PDFs should be where the classroom polish lives.
- Avoid ugly embedded PDF previews unless they are just optional links. Prefer buttons, preview cards, thumbnails, or HTML-rendered module summaries.

**The website is the control panel.**
**The PDF is the classroom tool.**
**The chatbot will eventually be the editor.**
