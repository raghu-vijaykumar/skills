# Restoration command examples

The README contains real, method-specific picture examples for the seven
visual correction methods. `refine` is a settings-selection and timeline
analysis route, so its evidence is the command and report contract below.

```powershell
python content-studio/skills/content-studio-video/edit/restoration/scripts/refine.py --timeline <edit-timeline.json> --output-timeline <refined-timeline.json> --report <refine.json>
```

`deblur` is marked unsupported and has no script. Conservative sharpening cannot
recover missed focus.
