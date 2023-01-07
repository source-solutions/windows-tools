# Windows Tools
A collection of x86 binary tools for use with the Chloe 280SE.

These tools will work on Windows (i386 and AMD64 architecture) and Windows 11 (ARM). The should also run on WINE under Linux (i386 and AMD64). On macOS they will work in a Windows 11 (ARM) virtual machine. They may work under WINE although you may find it easier to use [CrossOver](https://www.codeweavers.com/crossover#requirements). Some of these tools are also available on Linux and macOS. Where tools are not provided as part of this repository, they are available from the links in the following list.

## Emulators

### Retro Virtual Machine

[Retro Virtual Machine](https://static.retrovm.org/release/beta1/windows/x86/RetroVirtualMachine.2.0.beta-1.r7.windows.x86.zip) emulates the ZX Uno hardware that the Chloe firmware runs on. It is the preferred user environment for running Chloe 280SE apps in emulation.

### ZEsarUX

[ZEsarUX](https://github.com/chernandezba/zesarux/releases/download/ZEsarUX-10.2/ZEsarUX_windows-10.2-legacy.zip) is the preferred development environment for writing apps for the Chloe 280SE.

## Audio

### Arkos Tracker II

[Arkos Tracker II](https://www.julien-nevo.com/arkostracker/) enables you to create six-channel tracker music for the Chloe 280SE. It can also import MIDI and Vortex Tracker II files.

### Ay_Emul

[Ay_Emul](https://bulba.untergrund.net/emulator_e.htm) is a music player and converter that supports the AY-3-891x and YM2149F sound chips. It can convert `SNDH` files for the Atari ST to `YM6` format which can be converted to play on the Chloe 280SE. Export is done by right-clicking the music in the play list.

### Vortex Tracker II

[Vortex Tracker II](https://github.com/ivanpirog/vortextracker/releases) enables you to convert 6 channel music in `PT3` format to its own native format which can then be imported into Arkos Tracker II. You can also use it to create and edit 6 channel music, but Arkos has a nicer interface.

### Ym2Mym

[Ym2Mym](https://osdk.org/index.php?page=documentation&subpage=ym2mym) converts `YM6` register dump files to the `MYM` format that can be played on the Chloe 280SE. It can also pitch shift the register values if the input file was designed for a chip with a different clock speed. Normally `YM6` files are stored as `LHA` archives and must be decompressed before conversion. Most decompression tools can handle the `LHA` format.

`Ym2Mym -r2 -t1.75 input.ym output.mym`

This will convert the an input `YM` file designed for a 2MHz PSG to an `MYM` output file and shift the register values for the Chloe 280SE's 1.75MHz sound chip.

## Cross-assemblers

### PASMO

[PASMO](https://pasmo.speccy.org/) is a simple Z80 cross-assembler. It is used to build Chloe 280SE apps.

### RASM

[RASM](https://github.com/EdouardBERGE/rasm/releases) is a fast Z80 cross-assembler with many features. It is used to build the Chloe 280SE firmware. It has online [documentation](http://rasm.wikidot.com/english-index:home).

## Fonts

### Bits'N'Picas

[Bits'N'Picas](https://github.com/kreativekorp/bitsnpicas) is a [Java](https://www.java.com/en/download/) app that enables you to edit monospaced and proportional bitmap fonts.

### FZX Font Editor

The FZX Font Editor enables you to edit monospaced and proportional bitmap fonts.

## Graphics

These tools are useful when converting images to the Chloe 280SE's legacy hi-color image format (256 x 192 pixels, 8 x 1 attributes, 64 colors).

### DaDither

[DaDither](https://www.dadither.com/) provides the best conversion of 24-bit images, with wide a choice of dither methods and batch conversion support. it has support for grayscale conversion (4 color). You can also force a fixed 17 color palette, which can be useful for video conversion. Downloads are available for [i386](https://www.dadither.com/bin/DaDither.exe) and [AMD64](https://www.dadither.com/bin/DaDither.64.exe) architectures.

### FFmpeg

[FFmpeg](https://ffmpeg.org/) enables you to convert video to individual frames at the correct size.

`ffmpeg -i foo.avi -r 30 -s 256x192 -f image2 foo-%03d.jpeg`

This will extract 30 video frames per second from the video and will output them in files named foo-001.jpeg, foo-002.jpeg, and so on. Images will be rescaled to fit the new 256×192 values.

### Image2ULAplus

Based on the earlier SCRplus, Image2ULAplus is an alternative to DaDither. It has limited dithering and no batch processing, but it can be useful in converting non-photo realistic images.

### ImageMagick

[ImageMagick](https://imagemagick.org/script/download.php#windows) is a bulk image processor. Most of the time, dithering with DaDither will give the best image results when converting from 24-bit images. But sometimes, pattern dither will give better results.

`magick input.jpg -resize 256x192\! -ordered-dither o8x8,5,5,4 output.gif`

This scales the image to 256×192 (ignoring the aspect ratio) and then performs an ordered (pattern) dither on the image using an 8×8 pattern (which works well with 8×1 attributes). It applies a uniform palette with 5 levels of red and green, and 4 levels of blue (128 uniform colors in Photoshop gives approximately 5 levels for each color). The results vary, but for the test image that I’ve used in all my tutorials, Image Magick actually does a better job than Photoshop. This is the optimal setting for use with Image2ULAplus. But for DaDither (with no dither selected) you could try `o8x8,8,8,4` to use the full G3R3B2 palette.

### ZX-Paintbrush

ZX-Paintbrush enables you to create and edit hi-color images. It's great for touching up converted images, adding attribute color to monochrome images or creating original artwork.
