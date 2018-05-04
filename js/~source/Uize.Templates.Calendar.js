/*
	This is an automatically generated module, compiled from the JavaScript template file:
		Uize.Templates.Calendar.js.jst
*/

/*ScruncherSettings Mappings="=" LineCompacting="TRUE"*/

Uize.module ({
	name:'Uize.Templates.Calendar',
	builder:function () {
		var _package = function () {};

		/*** Public Static Methods ***/
			_package.process = function (input) {
				var output = [];
				/* Module Meta Data
					type: Template
					importance: 2
					codeCompleteness: 100
					testCompleteness: 0
					docCompleteness: 100
				*/
				/*?
					Introduction
						The =Uize.Templates.Calendar= module generates HTML that can be used for instances of the =Uize.Widget.Calendar= class.

						*DEVELOPERS:* `Chris van Rensburg`

						The =Uize.Templates.Calendar= module is a JavaScript Template Module that is automatically generated by a build script from a companion =Uize.Templates.Calendar.js.jst= JavaScript Template (.jst) file.

					Public Static Methods
						Uize.Templates.Calendar.process
							Returns a string, being the generated HTML that is to be used by an instance of the =Uize.Widget.Calendar= class (or subclass).

							SYNTAX
							...........................................................
							widgetHtmlSTR = Uize.Templates.Calendar.process (inputOBJ);
							...........................................................

							The value of the =inputOBJ= parameter should be an object of the form...

							........................
							{
								idPrefix: idPrefixSTR
							}
							........................

							idPrefix
								A string, specifying the value of the =idPrefix= set-get property of the widget instance that uses this module to generate its HTML.

					Public Static Properties
						Uize.Templates.Calendar.input
							An object, describing the allowed properties of the =inputOBJ= parameter of the =Uize.Templates.Calendar.process= static method.
				*/
				output.push ('<div class="calendarContainer">\r\n	<div id="',input. idPrefix,'-controls" class="calendarControls">\r\n		<div id="',input. idPrefix,'-indicator" class="calendarIndicator">\r\n			<span id="',input. idPrefix,'-month" class="monthIndicator">Month</span>\r\n			<span id="',input. idPrefix,'-year" class="yearIndicator">Year</span>\r\n		</div>\r\n		<a href="javascript://" id="',input. idPrefix,'_previousMonth" class="calendarControl previousMonth" title="previous month">&#9668;</a>\r\n		<a href="javascript://" id="',input. idPrefix,'_nextMonth" class="calendarControl nextMonth" title="next month">&#9658;</a>\r\n		<a href="javascript://" id="',input. idPrefix,'_previousYear" class="calendarControl previousYear" title="previous year">&laquo;</a>\r\n		<a href="javascript://" id="',input. idPrefix,'_nextYear" class="calendarControl nextYear" title="next year">&raquo;</a>\r\n	</div>\r\n	<div id="',input. idPrefix,'-grid" class="calendarGrid"></div>\r\n</div>\r\n');
				return output.join ('');
			};

		/*** Public Static Properties ***/
			_package.input = {
				idPrefix:'string'
			};

		return _package;
	}
});

