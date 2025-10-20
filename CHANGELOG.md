Development Notes: by L.Sumireneko.M

## Late August in last year 2024
* Earlier experiment. Imprement of the initialy offset routine. Primive bezier curve(Display Normal) by Javascript
* Because it could rappidly try and error test
* Apply offset to single bezier curve
* Create round cap,it set up from a line-end/start
* But it seems that conneted However, these lines were not connected in appearance. When you put them all together, you'll notice that the lines are connected in a strange order.
* It can only be applied to a single Bezier curve and is not very versatile.
* But It is useless if followed by another path command.

* try again
* Goal: To offset a broken line path.
* I decided to load multiple commands from the beginning and apply them.
* It is very difficult to do this when curves and lines are mixed, so for now you have to give up on offsetting the handles of Bezier curves.
* I have no choice but to proceed with implementing only the lines.
## Jan. 2025?
* Offset connection (first completion)
* Implement of LineCAP type,round,miter and bevel
* Connect each offset line to its intersection.
* Draw and test path lines at various angles.
* Simplify using the rdp algorithm
* Debugging with point and tangent plots.
* Adopts detection of corners by curvature
* LineCAP type implementation (reworked)
* Added sample objects (line, circle, rect, etc.)
* Process lines, circles, and rects separately
* Support polygon and polyline
* Use the A command (arc) to round the corners of a rect
* Support open and closed path 
* Outline and offset branching
* Importing data tests in inkscape and illustrator (avoid crash at Adobe Illustrator)
* Implemented miter angle ratio (rate=4, cut off corners if they are 4 times the linewidth)
## April 2025
* Started porting to Python (changed function names, arguments, number of arguments, etc.)
* At that time, passes would sometimes arrive and sometimes not depending on the length of the line.
* Make it applicable to multiple objects.
* Treat cap as LineCAP and CornerCAP
* Implemented path length and path data functions that exist in JavaScript but not in Python.
* Support for HVCSQLA commands
* LineProfile implementation (tapered, double tapered, half, cycloid), arrow cap added

* I was able to get the outline, but I was plagued by issues with the coordinates and scale being misaligned.

* LineCAP doesn't connect well. Cut off unnecessary coordinates at the tip.
* Fix the missing end of the line (the argument for was wrong so the line only went halfway)
* Add the layer scale to the absoluteTransform and place it at the same position (as a nice side effect, it helps with accurate debug display coordinates)
* Subpath object support
* A corner was missing. --> Fix the issue where subpath commands were not parsed (Q, S, C, etc.).
* Check for oversight of HVCSQLA commands
* Test by offsetting the subpath offset lines further.
## April 11, 2025
* Eliminate the self-intersecting path problem (if this is not resolved, it cannot be called an outline.)
* The loop of the last self-intersecting path of a closed path cannot be resolved -> Manually reconnect the last part
* The Miter offset regression, so I adjusted the parameters to fix it somewhat.
* In PyQt's SVG, if there are two or more commands with the same coordinates at a corner, unintended curves will occur, so I removed the duplicate points.
* The tip CAP processing rechecked.
* Fixed an issue where the Bezier command became a line command as a side effect of the function to remove unnecessary points.s
* Beautiful cap restored
  * Refactoring function arguments (grouping style-related arguments together)
  * Adjust to get the right results (fill and line color, thickness behavior, vertex connection order)
  * params vs orig_elm
  * outline Outline command. Erase the original. Color etc. OK

* Line profile. It basically has a period. It is sharpened within the period. Is it possible to make wavy lines by shifting the period?
* Is it possible to make zigzag lines? (sine wave, square wave)s
* offset
  * Allows to select the right and left line caps separately
  * Fix the connection of arrow vertices when the line cap is on one side
  * Arrow end point, linear direction in two ways (I'm wondering whether to combine them into one)
  * [Oversight] The x-axis scaling of the line profile has been changed to 4x as a basic value so that the tip can be displayed.
  * Examination of necessary points for line profile and butt (ad hoc)

* Offset (only one outer path?)
* What to do if there are multiple subpaths?
* Preview
  * Basically it doesn't replace anything (it's easy because you just add new ones)
  * Additional feature...
    * Group them together as a mutable temporary group?
    * It can remove if groups all at once
  * Preprocessing by calling select_shaped process() (again) (remove the temporary group if there is one).
  * When confirmed (taken out of temporary group)
  * When canceled (delete temporary group)

* I stopped using temporary groups, and used id + uuid instead.
* outline works
* offset doesn't work
* event fires.
* determine doesn't erase X temporary shape.
* re_init doesn't erase X temporary shape.
* miter edge is cut off (C upper coordinate cut off?).

## May 2025
* Temporary id = uuid shapes do not disappear.
* Connected to GUI for integration test.
* Switched between displaying and hiding preview objects.
* Miter line ends were inappropriate, so created based on square.
* Path from line element generated an error, so fixed it.
* Improved edge cases of line_vector. (Direction vectors point in the same position and direction for short straight lines)
* An error occurred in short cases like line, so in that case taper was made unsupported.
* Flag was turned OFF at startup, and preview was executed when the dialog was opened.
* Corrected offset parameter to a relative value indicating how much to ± the width of the original object.
* Automatic preview is only performed once when the dialog is displayed after launch, so turn off the flag when you close the dialog.
* Make the preview work when you return focus.
* Outline. Multiple subpaths. Is it possible to create a dotted outline by dividing a straight line? It seems to be a heavy process.
* KritaPythonTool was helpful.
* Carefully reviewed CAP connection. Ensured it was for closed lines.
* Improved the perfection of taper mode, but there was no consistency and it was not possible to give comprehensive parameters.
* Eventually, scale and other things broke and it stopped working properly.
* Adjusted each taper mode so that it would produce a visible change depending on the Factor value.
* It was difficult to make it possible to constantly see the increase or decrease in shape in these modes.
* Abolished some modes that had mixed results.
* Suppressed (but reduced) the phenomenon that some taper coordinates were skipped.
* When taper mode was enabled, the inner lines disappeared.
* Therefore, the conditions for self-intersection of the path were tightened to prevent them from disappearing.
* Improved UI visibility (highlighting using CSS, etc.)
* Linked sliders and spin boxes, measures to prevent crashes due to excessive events.
* Fixed a bug where the miter cap connections on a single line segment were inconsistent.
## June 2025
* In subtle cases close to a straight line, if the array becomes 0, it is treated as a straight line and falls back.
* Use rdp to simplify excessive vertices created by tapers.
* Added point-connecting mode.
* Segfault11 problem: frequent crashes. Logs reveal select-related bugs, slider signals not being properly disconnected.
* Started in console, got unknown print output log after GUI incorporation.
* Segfault11 error occurs when quitting Krita v5.2-5.3 with any shape selected.
* Segfault11 revealed that deselect() was involved. Use shape.deselect() to take temporary action.

* Implemented point-connecting mode to check connection problems, plotting outp lp lp2 makes it easier to find the cause.
* Problem of outp going out of range will be addressed by checking outside of rectangle.
* Problem of lp going out of range.
* Problem of ofs2 overlapping with ofs in some parts. Should I just delete ofs2? Gear etc.

* Refactoring
* Fixed the problem with the original lines not working.
* Added Sigma Onion Brush.
* Troubled by connection and crashing issues.
* Trouble with points I want to erase not disappearing.
* Made it possible to find and display the center coordinates of the bounding box (for debugging).
* Self-intersection detection
* Reduced the occurrence of segfaults. Updated GUI sliders and spin boxes. Fixed so that it works when the value fluctuation is above a certain amount.
* Fixed the problem with self-intersection not working properly by reviewing the parameters.
* Adjust the size of the line-cap shape for tapered lines (variable size cap).
* Review the tapered shape.
* Make the tapered tip of linear_a tapered at both ends.
* Consider whether it is possible to implement a calligraphy-style brush shape.
* The mode that makes use of the original line may be useful for shadows. ,
* Eliminate the troublesome regression errors that occurred through trial and error with two points (one segment) one by one.
* What to do about the irregular case + effect of two points (one segment)? Handling boundary data.
* Applied to polylines with 2, 3, 4, 5 points, and test data such as polygons, rectangles, and ellipses.
* The debug display is useful, but it is frustrating when coordinates that should be there are not actually added.
* Improve debugging efficiency by using the miter_limit value. Find the conditions under which bugs occur.

* Fixed a problem where 2-point (one segment) line caps were not connected properly. It was a pain.
* Fixed a bug in connect-the-dots where the last coordinate of a polyline with 4 or less points was not plotted. It was a pain.
* Fixed a bug in connect-the-dots where a 2-point (one segment) line was not plotted. It was a pain.

* A 2-point (one segment) line is too short, so effects such as taper are disabled (however, dot_to_dot and OriginalLine are supported)
* Occurs when Arrow and onesegment are combined

* Effect (11) * Cap type (10x2) * Corner type, original Line Mode
* Shape or Path, opened/closed, cross/nocross, is the connection at a corner?

## July.2025
* Reverse cap of linear is difficult (open path).
* Multiple M commands can be created, connected in strange places, looks nice, but color leaks when fill is set.
* Use online SVG editor, Inkscape, marker to understand the flow of the path.
* Frequently save SVG data to analyze the generated path with other tools. I'm glad I made a plugin to save the selected svg shape.
* Refactored the CAP generation function, tried a function to reverse the CAP array, but ended up not using it (actually, it will be used later).
* Clarify the connection points. Check if there are multiple M commands just before connecting open path.
* Only reworked the cap connection part.

* Extends Krita's line_dash to support dotted dashes (0 is fine in browsers, but in PyQt's SVG, dots will not appear unless you give a tiny value of 0.001)
* Adds random_dash and dynamic_dash

* Regression bug? line_join behaves strangely (round corners are not rounded, bevel corners are not cut)
* Reverted rdp parameters to previous version
* Bevel corner cutting is now clearly handled separately (for skips and curvature detection).
* Set stroke-miterlimit to 3 (because in PyQt's SVG, if vertices are at the same coordinates, they are pushed together, making the lines rough or drawn in a strange direction)

* The smoothness of linejoins can now be adjusted with a factor.
* Filling can now be checked in FillView mode.
* Preview colors can now be freely selected using the color selector.
* Fixed the problem of freezing when the dash-array value became negative when factor=0.

* Fixed the disorder of Paths connection in the close shape of circle and ellipse variants (removed the last coordinate of d1)

* Added Reverse mode to reverse the line direction. This reverses the order of cmd and points in pData. This was the breakthrough.
* Thanks to the Reverse mode, the burden of the linear and linear_a problems was significantly reduced.
* This allowed to refactor the single sent.
* This refactoring broke the consistency of the code that had been working up until then, and the cap problem resurfaced.
* Separately from this, a bug occurred where dash and cap were not consistent (discovered when using Arrow). In that case, copy to the dash parameter and treat Taper as None.
* However, if dash is not specified, always set it to None to address the issue.
* Repeated trial and error.
* The order of the Arrows in cap-a was reversed, so reversed it.
* To make the cap problem consistent...for some reason, it was finally fixed when single segment was made to correspond to variable size cap.
* I decided to make dash and cap consistent using the Normalized cap order of the generate_cap_data() function.

* About refactoring:
 * I was finally able to remove the biggest concern, which was dividing the part that calculates the offset coordinates and the part that connects the CAP with large-scale branches and functions depending on whether it is single_segment or not.
 * I was able to fix the handling of single_segment so that it is handled with the minimum amount of code.
 * There are still some parts of the code that are clutter and some debug code left, but I will clean them up and divide them into functions later.
 * generate_cap_data() and generate_outline_path() are the most clutter.
 * As a side effect, there was an issue where the CAP collapsed when it was single_segment and organic, so I fixed it (d1, d2 coordinates are not deleted).

* Redo the closed path processing... I decided to connect it simply for now.
* If the offset of the first and last paths of rough is 0, a correction is made to bring it closer to the max.
* For Ellipse and Circle, a workaround has been added to the issue where unintended garbage coordinates remain at the start and end points when a forced effect is applied. It doesn't have much effect though.
* If there are multiple subpaths, only the even-numbered subpaths are left, making it possible to extract only the original path even if they are alternated by offsets.

## 2025 7/16 6:48

* Reduce the resolution of linejoin round. Reduce points to some extent only in rough mode.
* Single path mode (only keep the longest path)

* It's very troublesome because the previous code is causing problems. If I fix one thing, it will affect the others!?
 * Decided to remove the inner self-loop when converting a Closed Rectangle to a Path.
 * This caused the corners of the Closed Round to remain, so I fixed that.
 * Once again, it crashed in the Closed Gear style, so I fixed that.
 * This caused the teeth of the Closed Gear to disappear, so I didn't go through remove_self_intersections, and set min 2 to max 150.
## 2025 7/21
 * This time, I fixed an error in fluffle. (Because I had been cutting the array too much, it was out of index.)
 * Remove unnecessary segment issues in Linear_a.

 * Add lock mechanism to re_init(),rm_shape(),process_main() for fix GUI update crash issue
   Use import traceback;traceback.print_stack() and import faulthandler;faulthandler.enable()

 * After solving the GUI update problem, a hidden fatal error appeared because the update frequency was skipped.
 * It freezes in complex cases (cases where the shape is like kanji and the size is changed with Transform). It happens frequently when the offset is changed to -1,0,1.
 * The cause was discovered. Validated with the clean_path_data() function. The SVG data contained a huge value like 1.23e+06,
   so it probably took a long time for Krita to allocate the virtual canvas area for the bitmap. Skipped. Maybe it's the connection in the upper left corner. Need to look into it.
 * After that fixes, lines were no longer displayed on circles and ellipses (None mode), so fixed that ;_;.
 * The code for error detection and try catch made spagetti code. so I had to do something about it.
## 2025 7/24
 * Reconsidered the contribution of the factor parameter in linear and linear_a. Made it so that the line is consistently thicker from start to finish.
 * Also made it apply to shapes within the g (Groups) tag. In this case, the results are also grouped. Also, it is correct not to add transform to the g tag.
 * Issue fixed that try-catch removing regression,ofs_shapes is none due to dot_to_dot mode.
 * Fixed it also the case of g (Groups)
 * Add varibale font size in taper_mode == dot_to_dot style, Add a counting method (all point increase)
 * Fixed a bug that caused a crash when closing a dialog while in dot_to_dot mode.
## 2025 7/28
 * Abandoned the method using Symbol and Use tags. Krita doesn't support them. Can't solve the problem when links break.
 * Implemented "stamp_top_group". This aligns shapes along a path.
 * Added point rotation information to pData.
 * Accumulate aligned shapes using a route in "dot_to_dot" mode.
 * Use transform to place them in the correct position.
 * Group them to make them easier to handle.
 * Make the frontmost group shape the key shape and align it to the path.
 * Make the frontmost group shape among the selected shapes the key shape and align it to the path.
## 2025 7/30
 * In "stamp_top_group mode ,add subdivide function of line segment and rectangle (return dict key={x,y,and angle})
 * In "stamp_top_group mode ,Adjustment of parameters.The number of line divisions can now be adjusted using the clean_intersections function.
## 2025 8/01
 * Check the transform for the arranging process.
 * When arranging circles and ellipses,It seems possible to do this by finding the circumscribing polygon and rotation angle of the circle.
 * When arranging paths, It simply thinned them out.
 * Changed to using Path when arranging in an ellipse.
 * Intermission
## 2025 8/11
 * Add new stamp function,then remove former functions
 * Add random and linear scale feature to stamp_top_groups
 * Check for Segfault 14 Illeagal instruction 4 
 * Set max stamp number to 80
## 2025 8/12
 * Add Custom UI change for stamp_top_groups mode
## 2025 8/14
 * Minor code modifications (removing unnecessary processing)
 * Manual enhancements and add troubleshooting.
 * Fixed the issue where the rounded corners of the outer offset of rect were not displayed.
## 2025 8/15
 * Support corner rounds rx,ry of the rectangle
 * Fixed the issue where the outline of circle and ellipse were not displayed.
## 2025 8/21
 * Fix the error that in Krita 5.2.0 on Windows 10 Pro,RuntimeError: sys.stderr is None<br>Thanks to Michelist for the feedback about the error.

## 2025 10/19
* Tested by Krita v5.2.14(PyQt5 with Python 3.13)
 * Preliminary PyQt6 compatibility added Updated import logic to support PyQt6 for future Krita 6.x compatibility.
 * Note: PyQt6 functionality has not been tested yet. This change is preparatory and not guaranteed to be stable.


## Known issues:
 * There is a possibility that Krita crashes with Segfault 11 If move the slider too intensely,(in stamp_top_groups mode,etc)


## Special Thanks to helpful information：
* [Krita Scripting school](https://scripting.krita.org/lessons/reference-api-krita)
* [Krita API Reference](https://api.kde.org/krita/html/classKrita.html)
* [Trigonometry algorithm: polygon offsetting(miter)](https://math.stackexchange.com/questions/1993951/trigonometry-algorithm-polygon-offsetting)
* [An algorithm for inflating/deflating (offsetting, buffering) polygons](https://stackoverflow.com/questions/1109536/an-algorithm-for-inflating-deflating-offsetting-buffering-polygons)
* [SVG dilate/erode filter vs. Illustrator Offset Path](https://stackoverflow.com/questions/12702955/svg-dilate-erode-filter-vs-illustrator-offset-path)
* [Tiller and Hanson algolithm: Control points of offset bezier curve ](https://math.stackexchange.com/questions/465782/control-points-of-offset-bezier-curve)
* [Mathcode](https://microbians.com/mathcode)
* [Microsoft copilot](https://copilot.microsoft.com/chats/)
* [Ramer–Douglas–Peucker algorithm](https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm)
* [Shapes and Layers Docker](https://github.com/KnowZero/Krita-ShapesAndLayers-Plugin)
* SvgPathEditor
  * [Github](https://yqnn.github.io/svg-path-editor/)
  * [SvgPathEditor demo](https://github.com/Yqnn/svg-path-editor)
* [SvgPathVisualizer]( https://svg-path-visualizer.netlify.app)
* [一から学ぶベジェ曲線|POTD](https://postd.cc/bezier-curves/)
* [ベジェ曲線入門]( https://pomax.github.io/BezierInfo-2/ja-JP/index.html)
* [svg要素の基本的な使い方まとめ](http://defghi1977.html.xdomain.jp/tech/svgMemo/svgMemo_12.htm)
* [ベジェ曲線のオフセットを計算する](https://zenn.dev/inaniwaudon/articles/2c01b38eb447b9)
* [コロキウム室(Bezier曲線の問題)](http://www.junko-k.com/cthema/44bezier.htm)
* [曲線の定性的扱いと自己交差性の判定](https://ist.ksc.kwansei.ac.jp/~ktaka/LABO/DRAFTS/PRO2024takahashi.pdf)
* [自己交差をなんとかしたい...という話](https://qiita.com/vxlxv54/items/850c9347b0843cdddbac)

