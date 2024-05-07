<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:reg="http://www.gov.bc.ca/2013/legislation/regulation"
                xmlns:bcl="http://www.gov.bc.ca/2013/bclegislation"
                xmlns:in="http://www.qp.gov.bc.ca/2013/inline"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                xmlns="http://www.w3.org/1999/xhtml"
                xmlns:oasis="http://docs.oasis-open.org/ns/oasis-exchange/table"
                xmlns:act="http://www.gov.bc.ca/2013/legislation/act"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                id="REG-HTML_1.0.xsl"
                exclude-result-prefixes="#default"
                version="2.0">

	  <xsl:strip-space elements="*"/>

	  <xsl:variable select="'false'" name="debugRegCurrency"/>

	  <xsl:output doctype-public="-//W3C//DTD HTML 4.0 Transitional//EN"
               doctype-system="http://www.w3.org/TR/html4/loose.dtd"
               encoding="UTF-8"
               indent="no"
               method="xhtml"/>

	  <!-- Import common BC Legislation Elements -->
	 
	<!-- make sure this is the line pushed up the stack -->
	<xsl:include href="http://standards.qp.gov.bc.ca/standards/BCLEG-HTML.xsl"/> 
	  <xsl:include href="http://standards.qp.gov.bc.ca/standards/DocNav.xsl"/>
 

	  <!-- **************************** VERSION 0.1 **************************** -->
	<!-- Added support for <centerheadnote> Needed to add linked 
			text to a pdf in the head of the document in the toc section of a 
			multi
	 -->

<!-- globalLink -->
	<xsl:variable select="'civix'" name="app"/>
	  <!--<xsl:variable name="aspect" select="'complete'"/>
	<xsl:variable name="index" select="'statreg'"/>-->
	<xsl:variable select="document('https://styles.qp.gov.bc.ca/media/qpDate.xml')"
                 name="dateFile"/>
	
	  <xsl:variable select="'abcdefghijklmnopqrstuvwxyz'" name="smallcase"/>
	  <xsl:variable select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'" name="uppercase"/>
	
	  <xsl:variable select="'http://standards.qp.gov.bc.ca/civix/document/id/regulationbulletin/regulationbulletin/regbulldates'"
                 name="regbulldates"/>
	  <xsl:variable select="'http://standards.qp.gov.bc.ca/civix/document/id/crbc/crbc/crbcLookup/xml'"
                 name="crbclookupdoc"/>
	  <!--<xsl:variable name="siteRoot" select="'http://test.bclaws.ca/civix/document/id/regcurrency/regcurrency/'"/>-->
	<!-- ********* Start of Template ***************** -->
	<xsl:template match="reg:regulation">

		    <xsl:choose>
			<!-- Here we determine wether we have a multiple
		page document, or not. We do this by counting the
		occurences or "content". Any more than 1, we assume
		it's a multipy page document -->
			
			<!--Full multi on one doc-->
			<xsl:when test="count(reg:content) &gt; 1 and (contains(@id, '_multi') or $isTestContent = 'true')">
				<!-- Multiple Page Document -->
				
				<!-- First we get the "pure" name of the file into a variable -->
				<xsl:variable select="substring-before(@index, '_multi')" name="filename"/>
				        <!-- Here we'll get the Alpha Character Representing the Folder it resides in -->
				<xsl:variable select="substring(normalize-space(title),1,1)" name="alpha"/>
				
				        <!-- Now we have our variables in line, we'll start by processing the
			Table of Contents -->
				
				<xsl:element name="html">
					          <xsl:attribute name="data-ismulti">
						            <xsl:value-of select="'true'"/>
					          </xsl:attribute>
					          <xsl:attribute name="id">
						            <xsl:value-of select="/reg:regulation/@id"/>
					          </xsl:attribute>
					          <head>
						            <META content="text/html; charset=utf-8" http-equiv="Content-Type"/>
						            <!--<META http-equiv="X-UA-Compatible" content="IE=8"/>-->
						<META http-equiv="X-UA-Compatible" content="IE=edge"/>
						            <title>Full Multi - <xsl:value-of select="reg:title"/>
                  </title>
						            <!-- css -->
						<link href="/standards/REGS-CSS.css" rel="stylesheet" type="text/css"/>
						            <!-- /css -->
						
						<script src="https://code.jquery.com/jquery-1.7.1.min.js"
                          type="text/javascript"/>
						            <script src="/standards/hitNav.js" type="text/javascript"/>
						            <xsl:apply-templates select="ccollect"/>
						            <script type="text/javascript">function launchNewWindow(url)
							{
							window.open(url,'','toolbar=1,scrollbars=1,location=0,statusbar=1,menubar=1,resizable=1,');
							}
							
							window.onload = function() {
								document.body.style.display = "block";
							}
						</script>
						            <style type="text/css">
							span.container {
							position: relative;
							}
							span.box {
							display: none;
							}
							a:hover+span.box, span.box iframe:hover, span.box:hover {
							display: block;
							z-index: 100;
							position: absolute;
							left: 10px;
							}
							#toolBar {
							position: fixed;
							top: 5px;
							left: 0;
							width: 100%;
							height: 25px;
							padding: 5px 10px;
							border-bottom: 3px solid #333; /* some styling */
							}
						</style>
						            <style type="text/css" media="print">
							#contentsscroll {
							height: auto;
							overflow-y: auto;
							}
							#toolBar {
							display: none;
							}
						</style>
						            <style type="text/css" media="screen">
							#contentsscroll {
							height: 90%;
							width: 98%;
							padding-left: 20px;
							margin-top: 40px;
							overflow: auto;
							}
							
							body {
							display: none;
							}
						</style>
					          </head>
					          <body bgcolor="#FFFFFF" text="#000000">
						            <xsl:call-template name="topBanner"/>
						            <div id="contentsscroll">
							              <xsl:call-template name="licenseHeader"/> 
							              <xsl:call-template name="htmHeaderRegulation"/>
							              <xsl:call-template name="htmTableContentsBCL"/>
							              <xsl:apply-templates select="*[not(self::reg:regnum[1] or self::reg:oic[1] or self::reg:effective[1] or self::reg:title[1] or self::reg:deposited[1] or self::reg:acttitle[1] or self::reg:amsincluded[1] or self::reg:NIF[1] or self::reg:NIFby[1] or self::reg:NIFdate[1] or self::reg:prerevisednote[1] or self::reg:defunct[1])] "/>
							              <xsl:apply-templates select="multinav"/>
							              <p class="copyright">Copyright © King's Printer, Victoria, British
								Columbia, Canada</p>
						            </div>
						            <!-- <xsl:call-template name="divEnd"/> -->
					</body>
				        </xsl:element>
			      </xsl:when>
			      <xsl:when test="count(reg:content) &gt; 1">
				<!-- Multiple Page Document -->

				<!-- First we get the "pure" name of the file into a variable -->
				<xsl:variable select="substring-before(@index, '_multi')" name="filename"/>
				        <!-- Here we'll get the Alpha Character Representing the Folder it resides in -->
				<xsl:variable select="substring(normalize-space(title),1,1)" name="alpha"/>

				        <!-- Now we have our variables in line, we'll start by processing the
			Table of Contents -->

				<xsl:element name="html">
					          <xsl:attribute name="data-ismulti">
						            <xsl:value-of select="'true'"/>
					          </xsl:attribute>
					          <xsl:attribute name="id">
						            <xsl:value-of select="/reg:regulation/@id"/>
					          </xsl:attribute>
					          <head>
						            <META content="text/html; charset=utf-8" http-equiv="Content-Type"/>
						            <META http-equiv="X-UA-Compatible" content="IE=edge"/>
						            <title>Table of Contents - <xsl:value-of select="reg:title"/>
                  </title>
						            <!-- css -->
						<link href="/standards/REGS-CSS.css" rel="stylesheet" type="text/css"/>
						            <!-- /css -->
						<link href="#!-- #ID:bcsansstylesheet.css --#"
                        rel="stylesheet"
                        type="text/css"/>

						            <script src="https://code.jquery.com/jquery-1.7.1.min.js"
                          type="text/javascript"/>
						            <script src="/standards/hitNav.js" type="text/javascript"/>
						            <xsl:apply-templates select="ccollect"/>
						            <script type="text/javascript">function launchNewWindow(url)
							{
								window.open(url,'','toolbar=1,scrollbars=1,location=0,statusbar=1,menubar=1,resizable=1,');
							}

							window.onload = function() {
								document.body.style.display = "block";
							}
							</script>
						            <script type="text/javascript">
							function showhide(elem) {
							var div = elem.nextSibling;
							while (div.nodeType!=1) {
							div = div.nextSibling;
							}
							if (div.style.display == 'block') {
							div.style.display = 'none';
							} else {
							div.style.display = 'block';
							}	
							}
						</script>
						            <style type="text/css">
							span.container {
							position: relative;
							}
							span.box {
							display: none;
							}
							a:hover+span.box, span.box iframe:hover, span.box:hover {
							display: block;
							z-index: 100;
							position: absolute;
							left: 10px;
							}
							#toolBar {
							position: fixed;
							top: 5px;
							left: 0;
							width: 100%;
							height: 25px;
							padding: 5px 10px;
							border-bottom: 3px solid #333; /* some styling */
							}
						</style>
						            <style type="text/css" media="print">
							#contentsscroll {
							height: auto;
							overflow-y: auto;
							}
							#toolBar {
							display: none;
							}
						</style>
						            <style type="text/css" media="screen">
							#contentsscroll {
							height: 90%;
							width: 96%;
							margin-left: 20px;
							margin-top: 40px;
							overflow: auto;
							}
							
							body {
							display: none;
							}
						</style>
					          </head>
					          <body bgcolor="#FFFFFF" text="#000000">
						            <xsl:call-template name="topBanner"/>
						            <div id="contentsscroll">
						               <xsl:call-template name="licenseHeader"/> 
						               <xsl:call-template name="htmHeaderRegulation"/>
						               <xsl:call-template name="htmTableContentsBCL"/>
						               <p class="copyright">Copyright © King's Printer, Victoria, British
							Columbia, Canada</p>
						            </div>
						            <!-- <xsl:call-template name="divEnd"/> -->
					</body>
				        </xsl:element>
			      </xsl:when>
			      <xsl:otherwise>
				<!-- Single Page Document -->
				<xsl:element name="html">
					          <xsl:if test="@isMulti">
						            <xsl:attribute name="data-ismulti">
							              <xsl:value-of select="'true'"/>
						            </xsl:attribute>
					          </xsl:if>
					          <head>
						            <META content="text/html; charset=utf-8" http-equiv="Content-Type"/>
						            <META http-equiv="X-UA-Compatible" content="IE=edge"/>
						            <title>
							              <xsl:value-of select="reg:title"/>
						            </title>

						            <!-- css -->
						<link href="/standards/REGS-CSS.css" rel="stylesheet" type="text/css"/>
						            <!-- /css -->
						<script src="https://code.jquery.com/jquery-1.7.1.min.js"
                          type="text/javascript"/>
						            <script src="/standards/hitNav.js" type="text/javascript"/>
						            <script type="text/javascript">
							function launchNewWindow(url)
							{
								window.open(url,'','toolbar=1,scrollbars=1,location=0,statusbar=1,menubar=1,resizable=1,');
							}
							window.onload = function() {
								document.body.style.display = "block";
							}
						</script>
						            <script type="text/javascript">
							function showhide(elem) {
							var div = elem.nextSibling;
							while (div.nodeType!=1) {
							div = div.nextSibling;
							}
							if (div.style.display == 'block') {
							div.style.display = 'none';
							} else {
							div.style.display = 'block';
							}	
							}
						</script>
						            <style type="text/css">
							span.container {
							position: relative;
							}
							span.box {
							display: none;
							}
							a:hover+span.box, span.box iframe:hover, span.box:hover {
							display: block;
							z-index: 100;
							position: absolute;
							left: 10px;
							}
							#toolBar {
							position:fixed;
							top:5px;
							left:0;
							width: 100%;
							height: 25px;
							padding: 5px 10px;
							border-bottom: 3px solid #333; /* some styling */
							}
						</style>
						            <style type="text/css" media="print">
							#contentsscroll{
							height: auto;
							overflow-y: auto;
							}
							#toolBar{
							display: none; 
							}
						</style>
						            <style type="text/css" media="screen">
							#contentsscroll{
							height: 90%;
							width: 98%;
							padding-left: 20px;
							margin-top: 40px;
							overflow: auto;
							}
							
							body {
							display: none;
							}
						</style>
					          </head>
					          <body bgcolor="#FFFFFF" text="#000000">
						            <xsl:call-template name="topBanner"/>
						            <div id="contentsscroll">
						               <xsl:call-template name="licenseHeader"/>
						               <xsl:call-template name="htmHeaderRegulation"/>
						               <xsl:if test="not(/reg:regulation/attribute::notoc)">
							                 <xsl:if test="not(//@toc='false')">
								                   <xsl:call-template name="htmTableContentsBCL"/>
							                 </xsl:if>
						               </xsl:if>
						               <xsl:apply-templates select="*[not(self::reg:regnum[1] or self::reg:oic[1] or self::reg:effective[1] or self::reg:title[1] or self::reg:deposited[1] or self::reg:acttitle[1] or self::reg:amsincluded[1] or self::reg:NIF[1] or self::reg:NIFby[1] or self::reg:NIFdate[1] or self::reg:prerevisednote[1] or self::reg:defunct[1])] "/>
						               <xsl:apply-templates select="multinav"/>

						               <!--<xsl:apply-templates select="provisionsnote"/>-->
						<p class="copyright">Copyright © King's Printer, Victoria, British
							Columbia, Canada</p>
						            </div>
						            <!-- <xsl:call-template name="divEnd"/> -->
					</body>
				        </xsl:element>
			      </xsl:otherwise>
		    </xsl:choose>
	  </xsl:template>




	  <!-- Here we have the template that spits out our header text -->
	<xsl:template name="licenseHeader">
		    <div id="header">
			      <table border="0" cellpadding="4" cellspacing="0" width="100%">
				        <tr>
					          <td class="sizesmall" valign="bottom">Copyright © King's Printer,<br/>
						Victoria, British Columbia, Canada</td>
					          <td align="right" class="sizemedium">
						            <a href="/standards/Licence.html">
							              <strong>Licence</strong>
						            </a>
						            <br/>
						            <a href="/standards/Disclaimer.html" target="_blank">
							              <strong>Disclaimer</strong>
						            </a>
					          </td>
				        </tr>
			      </table>
		    </div>
		    <!--add link to the full multi-->
		<xsl:if test="@isMulti and not(contains(@id, '_multi'))">
			      <xsl:variable name="oneFileMulti">
				        <xsl:value-of select="concat('/', $app, '/document/id/', $aspect, '/', $index, '/', replace(@index,'_multi','_00_multi'))"/>
			      </xsl:variable>
			      <p align="right" class="bold">
            <a href="{$oneFileMulti}">View Complete Regulation</a>
         </p>
		    </xsl:if>
	  </xsl:template>
	  <xsl:template name="htmHeaderRegulation">
		    <xsl:if test="*:regnum">
			      <table border="0" cellpadding="0" cellspacing="0" width="100%">
				        <tbody>
					          <tr>
						            <td class="sizetext1" valign="top">
							              <xsl:apply-templates select="*:regnum"/>
							              <xsl:apply-templates select="*:oic"/>
						            </td>
						            <td align="right" class="sizetext1" valign="top">
							              <xsl:apply-templates select="*:deposited"/>
							              <xsl:apply-templates select="*:filed" mode="title"/>
							              <xsl:apply-templates select="*:effective"/>
						            </td>
					          </tr>
				        </tbody>
			      </table>
		    </xsl:if> 
		    <xsl:if test="reg:defunct">
			      <p align="center">
				        <font color="red">
					          <strong>
						            <xsl:apply-templates select="reg:defunct"/>
					          </strong>
				        </font>
			      </p>
		    </xsl:if>

		    <xsl:if test="repealed">
			      <p align="center">
				        <font color="red">
					          <strong>
						            <xsl:apply-templates select="repealed"/>
					          </strong>
				        </font>
			      </p>
		    </xsl:if>				
		    <!-- not used in regs convienancehead -->
		<!--		<xsl:if test="/descendant::convienancehead">
			<p>
				<em>
					<xsl:apply-templates select="convienancehead"/>
				</em>
			</p>
			</xsl:if>-->
		<!--this was moved several lines down -->
<!--		<xsl:if test="/descendant::reg:prerevisednote">
			<p class="prnote">
				<xsl:apply-templates select="/descendant::reg:prerevisednote"/>
			</p>
		</xsl:if>-->
	
		<xsl:if test="$debugRegCurrency eq 'true'">
			      <br/>
			      <xsl:text>translatedID= </xsl:text>
			      <xsl:value-of select="translate(/reg:regulation/@id,$uppercase, $smallcase)"/>
		    </xsl:if>
	
		    <xsl:if test="not(contains(translate(/reg:regulation/@id,$uppercase, $smallcase), 'anif')) and not(/reg:regulation/reg:defunct) and not(/reg_pit)">
			<!-- REG CURRENCY -->
			<xsl:if test="/reg/currency">
				        <xsl:apply-templates select="/descendant::currency"/>
			      </xsl:if>
			
			      <!--<xsl:if test="(not(/reg:regulation/reg:NIF) and not(/reg:regulation/reg:defunct)) and (/reg:regulation/reg:regnum)">
					<span class="notice"><strong>Note:</strong> Check the Cumulative Regulation Bulletin
						2015 and 2016<br/>for any non-consolidated amendments to this regulation that may be in
						effect.</span>
				</xsl:if>-->
						
			<!-- Numerical value used for comparasons  -->
			<xsl:variable name="newestRegBullDate">
				        <xsl:call-template name="getNewestRegBullDate"/>
			      </xsl:variable>
			      <xsl:if test="$debugRegCurrency eq 'true'">
				        <br/>
				        <xsl:text>newestRegBullDate= </xsl:text>
				        <xsl:value-of select="$newestRegBullDate"/>
			      </xsl:if>
			
			      <!-- Printable version used for output -->
			<xsl:variable name="printableRegBullDate">
				        <xsl:call-template name="convertDateToPrintableDate">
					          <xsl:with-param name="passedDate" select="$newestRegBullDate"/>
				        </xsl:call-template>
			      </xsl:variable>
			      <xsl:if test="$debugRegCurrency eq 'true'">
				        <br/>
				        <xsl:text>printableRegBullDate= </xsl:text>
				        <xsl:value-of select="$printableRegBullDate"/>
			      </xsl:if>
			      <!-- Variables needed to calculate the differnt reg currencies -->
			<xsl:variable select="count(/reg:regulation/reg:amend[not(@added) and @bullId])"
                       name="numberOfNotAdded"/>
			      <xsl:if test="$debugRegCurrency eq 'true'">
				        <br/>
				        <xsl:text>numberOfNotAdded= </xsl:text>
				        <xsl:value-of select="$numberOfNotAdded"/>
			      </xsl:if>
			      <xsl:variable select="count(/reg:regulation/reg:amend[not(@added) and @bullId and @hasGreenSheet='yes'])"
                       name="numberOfNotAddedWithGreenSheetTrue"/>
			      <xsl:if test="$debugRegCurrency eq 'true'">
				        <br/>
				        <xsl:text>numberOfNotAddedWithGreenSheetTrue= </xsl:text>
				        <xsl:value-of select="$numberOfNotAddedWithGreenSheetTrue"/>
			      </xsl:if>
			      <!-- This variable counts the number of amend elemetnts with a bullId, who have hasGreenSheet='no' + the number of amend elemetnts with a bullId, who do not have a hasGreenSheet element -->
			<xsl:variable select="number(count(/reg:regulation/reg:amend[not(@added) and @bullId and @hasGreenSheet='no'])) + number(count(/reg:regulation/reg:amend[not(@added) and @bullId and not (@hasGreenSheet)]))"
                       name="numberOfMissingGreenSheets"/>
			      <xsl:if test="$debugRegCurrency eq 'true'">
				        <br/>
				        <xsl:text>numberOfMissingGreenSheets= </xsl:text>
				        <xsl:value-of select="$numberOfMissingGreenSheets"/>
			      </xsl:if>
			      <!-- Numerical value used for comparasons  -->
			<xsl:variable name="latestEffectiveDate">
				        <xsl:call-template name="getLatestEffectiveDate"/>
			      </xsl:variable>
			      <xsl:if test="$debugRegCurrency eq 'true'">
				        <br/>
				        <xsl:text>latestEffectiveDate= </xsl:text>
				        <xsl:value-of select="$latestEffectiveDate"/>
			      </xsl:if>
			      <!-- Printable version used for output -->
			<xsl:variable name="printableLastEffectiveDate">
				        <xsl:call-template name="convertDateToPrintableDate">
					          <xsl:with-param name="passedDate" select="$latestEffectiveDate"/>
				        </xsl:call-template>
			      </xsl:variable>
			      <xsl:if test="$debugRegCurrency eq 'true'">
				        <br/>
				        <xsl:text>printableLastEffectiveDate= </xsl:text>
				        <xsl:value-of select="$printableLastEffectiveDate"/>
			      </xsl:if>
		
			      <xsl:variable select="number(count(/reg:regulation/reg:amend[not(@added) and @bullId and @hasGreenSheet='no'])) + number(count(/reg:regulation/reg:amend[not(@added) and @bullId and not(@hasGreenSheet)]))"
                       name="countOfLatestEffectiveAmends"/>
			      <xsl:if test="$debugRegCurrency eq 'true'">
				        <br/>
				        <xsl:text>countOfLatestEffectiveAmends= </xsl:text>
				        <xsl:value-of select="$countOfLatestEffectiveAmends"/>
			      </xsl:if>
			
			      <!-- Building the text and link to the cumulative regbull.  Linking to multiple cumlative rebulls if needed -->
			<xsl:variable name="linkToCumulatiText">
				        <xsl:choose>
					<!-- In this case there is only 1 latestEffectiveDate found -->
					<xsl:when test="number($countOfLatestEffectiveAmends) eq 1">
						            <xsl:if test="$debugRegCurrency eq 'true'">
							              <br/>
							              <xsl:text>IN countOfLatestEffectiveAmends = 1</xsl:text>
						            </xsl:if>
						            <!-- Year of the regbull derived from the bullId attribute -->
						<xsl:variable select="substring-before(/reg:regulation/reg:amend[not(@added) and @bullId and @hasGreenSheet='no']/@bullId, 'bull')"
                                name="regBullYear"/>
						            <xsl:element name="a">
							              <xsl:attribute name="href"
                                    select="concat('http://www.bclaws.ca/civix/document/id/regulationbulletin/regulationbulletin/',$regBullYear,'cumulati')"/>									
							              <xsl:text>Cumulative B.C. Regulations Bulletin </xsl:text>
							              <xsl:value-of select="$regBullYear"/>
						            </xsl:element>
					          </xsl:when>
					          <!-- In this case there are more than 1 latestEffectiveDate found -->
					<xsl:when test="number($countOfLatestEffectiveAmends) &gt; 1">
						            <xsl:if test="$debugRegCurrency eq 'true'">
							              <br/>
							              <xsl:text>IN countOfLatestEffectiveAmends &gt; 1</xsl:text>
						            </xsl:if>
						            <!-- create a group for each distinct year -->
						<xsl:for-each-group select="/reg:regulation/reg:amend[not(@added) and @bullId and (@hasGreenSheet='no' or not(@hasGreenSheet))]/@bullId"
                                      group-by="substring-before(., 'bull')">
							
							<!-- Sorting based on the year -->
							<xsl:sort select="substring-before(., 'bull')" order="ascending"/>
							              <!-- Year of the regbull pulled from the current group -->
							<xsl:variable select="current-grouping-key()" name="regBullYear"/>
							              <xsl:if test="$debugRegCurrency eq 'true'">
								                <br/>
								                <xsl:text>current Year= </xsl:text>
								                <xsl:value-of select="$regBullYear"/>
							              </xsl:if>
							
							              <xsl:choose>
								<!-- Here we are in the 2nd cumulative text and link -->
								<!-- NOTE: Currently both the 1st and 2nd cumulative text and link contain the same text and link.  
													This is due to Rod possibly wanting the 2nd text to display differently.
													This can be modified if that is not the case.  -->
								<xsl:when test="position() ne 1">
									                  <xsl:text> and </xsl:text>
									                  <xsl:element name="br"/>
									                  <xsl:element name="a">
										                    <xsl:attribute name="href"
                                             select="concat('http://www.bclaws.ca/civix/document/id/regulationbulletin/regulationbulletin/',$regBullYear,'cumulati')"/>
										                    <xsl:text>Cumulative B.C. Regulations Bulletin </xsl:text>
										                    <xsl:value-of select="$regBullYear"/>
									                  </xsl:element>
								                </xsl:when>
								                <xsl:otherwise>
									<!-- Here we are in the 1st cumulative text and link -->
									<xsl:element name="a">
										                    <xsl:attribute name="href"
                                             select="concat('http://www.bclaws.ca/civix/document/id/regulationbulletin/regulationbulletin/',$regBullYear,'cumulati')"/>									
										                    <xsl:text>Cumulative B.C. Regulations Bulletin </xsl:text>
										                    <xsl:value-of select="$regBullYear"/>
									                  </xsl:element>
								                </xsl:otherwise>
							              </xsl:choose>
						            </xsl:for-each-group>
					          </xsl:when>
				        </xsl:choose>
			      </xsl:variable>
			
			      <!-- creating variables used to determine if the effective date is in the past or future  -->
			<xsl:variable select="format-date(current-date(), '[Y0001][M01][D01]')"
                       name="todaysDate"/>
			      <xsl:if test="$debugRegCurrency eq 'true'">
				        <br/>
				        <xsl:text>todaysDate= </xsl:text>
				        <xsl:value-of select="$todaysDate"/>
			      </xsl:if>
			      <xsl:variable select="translate($latestEffectiveDate, '-', '')"
                       name="effectiveDateForCompare"/>
			      <xsl:if test="$debugRegCurrency eq 'true'">
				        <br/>
				        <xsl:text>effectiveDateForCompare= </xsl:text>
				        <xsl:value-of select="$effectiveDateForCompare"/>
			      </xsl:if>
			
			      <!-- Determining our currencyDate based on if the effective date is in the past or not -->
			<xsl:variable name="currencyDate">
				        <xsl:choose>
					          <xsl:when test="number($effectiveDateForCompare) &gt;= number($todaysDate)">
						            <xsl:value-of select="$printableRegBullDate"/>
					          </xsl:when>
					          <xsl:otherwise>
						<!-- here we get the regbull date before the effective date -->
						<xsl:call-template name="convertDateToPrintableDate">
							              <xsl:with-param name="passedDate">
								                <xsl:call-template name="getPreviousRegBullDate">
									                  <xsl:with-param name="effectiveDate" select="$effectiveDateForCompare"/>
								                </xsl:call-template>
							              </xsl:with-param>
						            </xsl:call-template>
					          </xsl:otherwise>
				        </xsl:choose>
			      </xsl:variable>
			
			      <span class="regCurrency">
				        <strong>
					          <xsl:choose>
						<!-- Case #5 -->
						<xsl:when test="/reg:regulation/reg:amend[not(@added) and @bullId]/@retro">
							              <xsl:if test="$debugRegCurrency eq 'true'">
								                <br/>
								                <xsl:text>CASE 5</xsl:text>
								                <hr/>
							              </xsl:if>
							              <xsl:text>This consolidation is current to </xsl:text>
							              <xsl:value-of select="$printableRegBullDate"/>
							              <xsl:text>,</xsl:text>
							              <br/>
							              <xsl:text>except for retroactive amendments made by</xsl:text>
							              <br/>
							              <xsl:text>B.C. Reg. </xsl:text>
							              <xsl:value-of select="/reg:regulation/reg:amend[not(@added)]/@regnum[parent::reg:amend/@retro]"/>
							              <xsl:text>.</xsl:text>
						            </xsl:when>
						            <!-- Case #2 -->
						<xsl:when test="/reg:regulation/reg:amend[not(@added) and not(@retro) and @bullId] and ((number($numberOfNotAdded) = number($numberOfNotAddedWithGreenSheetTrue)) and (number($numberOfNotAdded) &gt; 0) and (count(/reg:regulation/reg:amend[not(@added)]/@retro) = 0))">
							              <xsl:if test="$debugRegCurrency eq 'true'">
								                <br/>
								                <xsl:text>CASE 2</xsl:text>
								                <hr/>
							              </xsl:if>
							              <xsl:text>This consolidation is current to </xsl:text>
							              <xsl:value-of select="$currencyDate"/>
							              <xsl:text>.</xsl:text>
							              <br/>
							              <xsl:text>See “Amendments Not in Force” for amendments</xsl:text>
							              <br/>
							              <xsl:text>effective after </xsl:text>
							              <xsl:value-of select="$currencyDate"/>
							              <xsl:text>.</xsl:text>
						            </xsl:when>
						            <!-- Case #3 -->
						<xsl:when test="/reg:regulation/reg:amend[not(@added) and not(@retro) and @bullId] and ((number($numberOfNotAdded) = number($numberOfMissingGreenSheets)) and (number($numberOfNotAdded) &gt; 0) and (count(/reg:regulation/reg:amend[not(@added)]/@retro) = 0))">
							              <xsl:if test="$debugRegCurrency eq 'true'">
								                <br/>
								                <xsl:text>CASE 3</xsl:text>
								                <hr/>
							              </xsl:if>
							              <xsl:text>This consolidation is current to </xsl:text>
							              <xsl:value-of select="$currencyDate"/>
							              <xsl:text>.</xsl:text>
							              <br/>
							              <xsl:text>See the </xsl:text>
							              <xsl:copy-of select="$linkToCumulatiText"/>
							              <br/>
							              <xsl:text>for amendments effective after </xsl:text>
							              <xsl:value-of select="$currencyDate"/>
							              <xsl:text>.</xsl:text>
						            </xsl:when>
						            <!-- Case #4 -->
						<xsl:when test="/reg:regulation/reg:amend[not(@added) and not(@retro) and @bullId] and ((number($numberOfNotAdded) - number($numberOfNotAddedWithGreenSheetTrue)) &gt;= 1) and ($numberOfNotAddedWithGreenSheetTrue &gt;= 1)  and (count(/reg:regulation/reg:amend[not(@added)]/@retro) = 0)">
							              <xsl:if test="$debugRegCurrency eq 'true'">
								                <br/>
								                <xsl:text>CASE 4</xsl:text>
								                <hr/>
							              </xsl:if>
							              <xsl:text>This consolidation is current to </xsl:text>
							              <xsl:value-of select="$currencyDate"/>
							              <xsl:text>.</xsl:text>
							              <br/>
							              <xsl:text>See “Amendments Not in Force” and the  </xsl:text>
							              <br/>
							              <xsl:copy-of select="$linkToCumulatiText"/>
							              <xsl:text> for </xsl:text>
							              <br/>
							              <xsl:text>amendments effective after </xsl:text>
							              <xsl:value-of select="$currencyDate"/>
							              <xsl:text>.</xsl:text>
						            </xsl:when>
						            <!-- Case #1 -->
						<xsl:when test="/reg:regulation/reg:amend/@added  and (count(/reg:regulation/reg:amend[not(@added)]/@retro) = 0)">
							              <xsl:if test="$debugRegCurrency eq 'true'">
								                <br/>
								                <xsl:text>CASE 1</xsl:text>
								                <hr/>
							              </xsl:if>
							              <xsl:text>This consolidation is current to </xsl:text>
							              <xsl:value-of select="$printableRegBullDate"/>
							              <xsl:text>.</xsl:text>
						            </xsl:when>
						            <!-- Catchall -->
						<xsl:otherwise>
							              <xsl:if test="$debugRegCurrency eq 'true'">
								                <br/>
								                <xsl:text>CASE CATCHALL</xsl:text>
								                <hr/>
							              </xsl:if>
							              <xsl:text>This consolidation is current to </xsl:text>
							              <xsl:value-of select="$printableRegBullDate"/>
							              <xsl:text>.</xsl:text>
						            </xsl:otherwise>
					          </xsl:choose>
				        </strong>
			      </span>
			      <!--  /REG CURRENCY -->
		</xsl:if>			
		    <!-- reg:prerevisednote -->
		<xsl:if test="/descendant::reg:prerevisednote">
			      <p class="prnote">
				        <xsl:apply-templates select="/descendant::reg:prerevisednote"/>
			      </p>
		    </xsl:if>
		
		    <xsl:if test="/descendant::statuterevision">
			      <p align="center" class="bold">
				        <xsl:apply-templates select="/descendant::statuterevision"/>
			      </p>
		    </xsl:if>
		    <xsl:if test="/reg/supplement">
			      <p align="center">
				        <strong>
					          <em>
						            <xsl:apply-templates select="/descendant::supplement"/>
					          </em>
				        </strong>
			      </p>
		    </xsl:if>
		
		    <xsl:call-template name="createDocumentlinks"/>
		
		    <xsl:apply-templates select="/descendant::reg:NIF"/>
		    <xsl:apply-templates select="/descendant::*:acttitle[1]"/>

		    <div id="title">
			      <h2>
				        <xsl:apply-templates select="/descendant::*:title[1]"/>
			      </h2>

			      <xsl:apply-templates select="/descendant::reg:NIFby"/>
			      <xsl:apply-templates select="/descendant::reg:NIFdate"/>
			
			      <xsl:choose>
				        <xsl:when test="/descendant::placeholderlink">
					          <xsl:element name="a">
						            <xsl:attribute name="href">#!-- #id=<xsl:value-of select="/descendant::placeholderlink"/> --#</xsl:attribute>
						            <h3>
							              <xsl:choose>
								                <xsl:when test="/descendant::yearenacted='1996'">[RSBC </xsl:when>
								                <xsl:otherwise>[SBC </xsl:otherwise>
							              </xsl:choose>
							              <xsl:apply-templates select="/descendant::yearenacted"/>] CHAPTER
								<xsl:apply-templates select="/descendant::chapter"/>
                  </h3>
					          </xsl:element>
				        </xsl:when>
				        <xsl:otherwise>
					          <xsl:if test="/reg:regulation/reg:yearenacted">
						            <h3>
							              <xsl:choose>
								                <xsl:when test="/descendant::reg:yearenacted='1996'">[RSBC </xsl:when>
								                <xsl:otherwise>[SBC </xsl:otherwise>
							              </xsl:choose>
							              <xsl:apply-templates select="/descendant::reg:yearenacted"/>] CHAPTER
								<xsl:apply-templates select="/descendant::chapter"/>
                  </h3>
					          </xsl:if>
				        </xsl:otherwise>
			      </xsl:choose>
		    </div>
		    <xsl:apply-templates select="/descendant::reg:amsincluded"/>
	  </xsl:template>

	  <!-- This template converts a date of the form yyyy-mm-dd to a printable date January 1, 2017 -->
	<xsl:template name="convertDateToPrintableDate">
		    <xsl:param name="passedDate"/>
		    <xsl:variable name="year">
			      <xsl:value-of select="substring-before($passedDate, '-')"/>
		    </xsl:variable>
		    <xsl:variable name="day">
			      <xsl:value-of select="substring-after(substring-after($passedDate, '-'), '-')"/>
		    </xsl:variable>
		    <xsl:variable name="month">
			      <xsl:call-template name="getPrintedMonth">
				        <xsl:with-param name="monthNumber"
                            select="substring-before(substring-after($passedDate, '-'), '-')"/>
			      </xsl:call-template>
		    </xsl:variable>
		    <xsl:value-of select="concat($month, ' ', number($day), ', ', $year)"/>
	  </xsl:template>

	  <!-- This template gets the newest effictive date that does not have an added, but has a bullId -->
	<xsl:template name="getLatestEffectiveDate">
		    <xsl:for-each select="/reg:regulation/reg:amend[@bullId and not(@added)]">
			      <xsl:sort select="./@effective" order="ascending"/>
			      <xsl:if test="position() = 1">
				        <xsl:value-of select="./@effective"/>
			      </xsl:if>
		    </xsl:for-each>
	  </xsl:template>

	  <!-- this template gets the most recent publication of the regbulls -->
	<xsl:template name="getNewestRegBullDate">
		    <xsl:for-each select="document($regbulldates)/*/regBullDate">
			      <xsl:sort select="number(./@year)" order="descending"/>
			      <xsl:sort select="number(./@month)" order="descending"/>
			      <xsl:sort select="number(./@day)" order="descending"/>
			      <xsl:if test="position() = 1">
				        <xsl:value-of select="./@year"/>
            <xsl:text>-</xsl:text>
            <xsl:value-of select="./@month"/>
            <xsl:text>-</xsl:text>
            <xsl:value-of select="./@day"/>
			      </xsl:if>
		    </xsl:for-each>
	  </xsl:template>
	
	  <!-- this template gets the most recent publication of the regbulls -->
	<xsl:template name="getPreviousRegBullDate">
		    <xsl:param name="effectiveDate"/>
		    <xsl:for-each select="document($regbulldates)/*/regBullDate[number(concat(@year, @month, @day)) &lt; number(translate($effectiveDate, '-', ''))]">
			      <xsl:sort select="number(./@year)" order="descending"/>
			      <xsl:sort select="number(./@month)" order="descending"/>
			      <xsl:sort select="number(./@day)" order="descending"/>
			      <xsl:if test="position() = 1">
				        <xsl:value-of select="./@year"/>
            <xsl:text>-</xsl:text>
            <xsl:value-of select="./@month"/>
            <xsl:text>-</xsl:text>
            <xsl:value-of select="./@day"/>
			      </xsl:if>
		    </xsl:for-each>
	  </xsl:template>
	
	  <!-- This template changes a numerical month to a printed month -->
	<xsl:template name="getPrintedMonth">
		    <xsl:param name="monthNumber"/>
		    <xsl:variable name="month">
			      <xsl:choose>
				        <xsl:when test="number($monthNumber)=1">
					          <xsl:text>January</xsl:text>
				        </xsl:when>
				        <xsl:when test="number($monthNumber)=2">
					          <xsl:text>February</xsl:text>
				        </xsl:when>
				        <xsl:when test="number($monthNumber)=3">
					          <xsl:text>March</xsl:text>
				        </xsl:when>
				        <xsl:when test="number($monthNumber)=4">
					          <xsl:text>April</xsl:text>
				        </xsl:when>
				        <xsl:when test="number($monthNumber)=5">
					          <xsl:text>May</xsl:text>
				        </xsl:when>
				        <xsl:when test="number($monthNumber)=6">
					          <xsl:text>June</xsl:text>
				        </xsl:when>
				        <xsl:when test="number($monthNumber)=7">
					          <xsl:text>July</xsl:text>
				        </xsl:when>
				        <xsl:when test="number($monthNumber)=8">
					          <xsl:text>August</xsl:text>
				        </xsl:when>
				        <xsl:when test="number($monthNumber)=9">
					          <xsl:text>September</xsl:text>
				        </xsl:when>
				        <xsl:when test="number($monthNumber)=10">
					          <xsl:text>October</xsl:text>
				        </xsl:when>
				        <xsl:when test="number($monthNumber)=11">
					          <xsl:text>November</xsl:text>
				        </xsl:when>
				        <xsl:when test="number($monthNumber)=12">
					          <xsl:text>December</xsl:text>
				        </xsl:when>
			      </xsl:choose>
		    </xsl:variable>
		    <xsl:value-of select="$month"/>
	  </xsl:template>
	
	  <!-- createregpitlink -->
	<xsl:template name="createDocumentlinks">
		<!-- CRBC Link -->
		<xsl:variable select="/*:regulation/@id" name="docID"/>
		
		    <!-- testing to see if we are in a multi.  If so we need to modify the id of the parts to ensure it matches with the PDF -->
		<xsl:variable name="isMultiTest">
			      <xsl:choose>
				        <xsl:when test="contains(/*:regulation/@index, '_multi')">
					          <xsl:value-of select="'true'"/>
				        </xsl:when>
				        <xsl:otherwise>
					          <xsl:value-of select="'false'"/>
				        </xsl:otherwise>
			      </xsl:choose>
		    </xsl:variable>
		    <xsl:variable name="multiIDForLookup">
			      <xsl:choose>
				        <xsl:when test="$isMultiTest eq 'true'">
					<!--<xsl:value-of select="concat(substring(/*:regulation/@id, 0, string-length(/*:regulation/@id) -2), '_00')"/>-->
					<xsl:value-of select="/*:regulation/@index"/>
				        </xsl:when>
			      </xsl:choose>
		    </xsl:variable>
		
		    <!--<xsl:choose>
			<xsl:when test="$isMultiTest eq 'true'">
				IS MULIT
			</xsl:when>
			<xsl:otherwise>
				IS NOT MULTI
			</xsl:otherwise>
		</xsl:choose>-->
		
		<!-- Testing to see if we can find a matching PDF in the lookup file -->
		<xsl:choose>
			      <xsl:when test="document($crbclookupdoc)//file[@id=$docID] | document($crbclookupdoc)//file[@id=$multiIDForLookup]">
				        <xsl:variable name="idToLookUp">
					          <xsl:choose>
						            <xsl:when test="$isMultiTest eq 'true'">
							              <xsl:value-of select="$multiIDForLookup"/>
						            </xsl:when>
						            <xsl:otherwise>
							              <xsl:value-of select="$docID"/>
						            </xsl:otherwise>
					          </xsl:choose>
				        </xsl:variable>
				        <xsl:variable name="pathToPDFDir">
					          <xsl:call-template name="getAncestorIDPath">
						            <xsl:with-param name="node" select="document($crbclookupdoc)//file[@id=$idToLookUp]"/>
						            <xsl:with-param name="idString" select="''"/>
					          </xsl:call-template>
				        </xsl:variable>
				        <xsl:variable name="crbcLink">
					          <xsl:value-of select="concat('/civix/content/crbc/crbc/', $pathToPDFDir ,'?xsl=/templates/browse.xsl')"/>
				        </xsl:variable>
				        <h5 align="center">
					          <strong>
						            <a href="{$crbcLink}">Link to consolidated regulation (PDF)</a>
					          </strong>
				        </h5>
			      </xsl:when>
		    </xsl:choose>
		
		    <!-- RegPIT Link -->
		<xsl:if test="/reg:regulation/reg:regpitid">
			      <xsl:variable name="regpitlink">
				        <xsl:choose>
					          <xsl:when test="$aspect eq 'roc'">
						            <xsl:value-of select="concat('/', $app, '/document/id/complete/statreg/', /reg:regulation/reg:regpitid[1])"/>
					          </xsl:when>
					          <xsl:otherwise>
						            <xsl:value-of select="concat('/', $app, '/document/id/', $aspect, '/', $index, '/', /reg:regulation/reg:regpitid[1])"/>
					          </xsl:otherwise>
				        </xsl:choose>
			      </xsl:variable>
			      <h5 align="center">
				        <strong>
					          <a href="{$regpitlink}">Link to Point in Time</a>
				        </strong>
			      </h5>
		    </xsl:if>
	  </xsl:template>

	  <!-- This template is used to build the path to the PDF reg.  It looks to each parent node to see if it is a directory and prepends its ID.  -->
	<xsl:template name="getAncestorIDPath">
		    <xsl:param name="node"/>
		    <xsl:param name="idString"/>
		    <xsl:choose>
			      <xsl:when test="$node/parent::directory">
				        <xsl:call-template name="getAncestorIDPath">
					          <xsl:with-param name="node" select="$node/parent::directory"/>
					          <xsl:with-param name="idString"
                               select="concat($node/parent::directory/@id, '/', $idString)"/>
				        </xsl:call-template>
			      </xsl:when>
			      <xsl:otherwise>
				        <xsl:value-of select="$idString"/>
			      </xsl:otherwise>
		    </xsl:choose>
	  </xsl:template>

	  <!-- reg:content -->
	<xsl:template match="reg:content">
		    <xsl:apply-templates/>
	  </xsl:template>

	  <!-- reg:regpitid -->
	<xsl:template match="reg:regpitid"/>

   <!-- reg:amsincluded -->
	<xsl:template match="reg:amsincluded">
		    <p align="center">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>



	  <!-- reg:NIF -->
	<xsl:template match="reg:NIF">
		    <div id="nif">
			      <h2>
				        <xsl:apply-templates/>
			      </h2>
		    </div>
	  </xsl:template>


	  <!-- reg:NIFby -->
	<xsl:template match="reg:NIFby">
		    <p align="center">
			      <strong>
				        <xsl:apply-templates/>
			      </strong>
		    </p>
	  </xsl:template>
	
	  <!-- reg:NIFdate -->
	<xsl:template match="reg:NIFdate">
		    <p align="center">
			      <font color="Red">
				        <em>
					          <xsl:apply-templates/>
				        </em>
			      </font>
		    </p>
	  </xsl:template>


   <!-- reg:acttitle -->
	<xsl:template match="*:acttitle">
		    <div id="actname">
			      <h2>
				        <xsl:apply-templates/>
			      </h2>
		    </div>
	  </xsl:template>
	
	
	  <!-- reg:Repealed -->
<!--	<xsl:template match="reg:repealedtext">
		<p align="center" field="repealedtext">
			<xsl:apply-templates/>
		</p>
	</xsl:template>-->

	<!--	<xsl:template match="supplement">
		<p align="center">
			<strong>
				<em>
					<xsl:apply-templates/>
				</em>
			</strong>
		</p>
	</xsl:template>-->


	<!-- reg:prerevisednote -->
	<xsl:template match="reg:prerevisednote">
		    <p class="prnote">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>


	  <!-- bcl:ccllect -->
	<xsl:template match="bcl:ccollect"/>

	  <xsl:template match="centerheadnote">
		    <p align="center">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>

	  <xsl:template match="multinav">
		    <p align="center">
			      <xsl:apply-templates mode="multinav"/>
		    </p>
	  </xsl:template>

	  <xsl:template match="navpage" mode="multinav">
		    <strong>
			      <xsl:choose>
				        <xsl:when test="attribute::currpage">
					          <xsl:value-of select="child::navtitle"/>
				        </xsl:when>
				        <xsl:otherwise>
					          <xsl:element name="a">
						            <xsl:attribute name="href">
							              <xsl:value-of select="child::navxmlfile"/>
						            </xsl:attribute>
						            <xsl:value-of select="child::navtitle"/>
					          </xsl:element>
				        </xsl:otherwise>
			      </xsl:choose>

			      <xsl:if test="following-sibling::navpage">  | </xsl:if>
		    </strong>
	  </xsl:template>

	  <xsl:template match="subheading" mode="toc">
		    <tr>
			      <td align="center" colspan="3" valign="top">
				        <strong>
					          <em>
						            <xsl:apply-templates/>
					          </em>
				        </strong>
			      </td>
		    </tr>
	  </xsl:template>

	  <!--	<xsl:template match="convienancehead">
		<xsl:apply-templates/>
	</xsl:template>
	-->
	


	<!--<xsl:template match="repealed">
		<xsl:apply-templates/>
	</xsl:template>-->

	<!-- reg:regum -->
	<xsl:template match="*:regnum">B.C. Reg. <xsl:apply-templates/>
   </xsl:template>

	  <!-- reg:oic -->
	<xsl:template match="*:oic">
		    <br/>
		    <span class="sizetext2">
			      <xsl:apply-templates/>
		    </span>
	  </xsl:template>

	  <!-- reg:deposited -->
	<xsl:template match="*:deposited">Deposited <xsl:apply-templates/>
      <br/>
   </xsl:template>

	  <!-- reg:effective -->
	<xsl:template match="*:effective">
		    <xsl:choose>
			      <xsl:when test="/descendant::red">
				        <span class="sizetext2">
					          <span class="red">effective</span>
					          <xsl:apply-templates/>
				        </span>
			      </xsl:when>
			      <xsl:otherwise>
				        <span class="sizetext2">effective <xsl:apply-templates/>
            </span>
			      </xsl:otherwise>
		    </xsl:choose>
	  </xsl:template>

	  <!-- reg:filed Mode=title -->
	<xsl:template match="*:filed" mode="title">
		    <span class="sizetext1">Filed <xsl:apply-templates/>
      </span>
		    <br/>
	  </xsl:template>

	  <!-- we dont want this element doing anything -->
	<!-- reg:filed -->
	<xsl:template match="*:filed"> </xsl:template>
	
	  <!-- reg:conveniencehead -->
	<xsl:template match="reg:conveniencehead">
		    <p>
			      <em>
				        <xsl:apply-templates/>
			      </em>
		    </p>
	  </xsl:template>

	  <!-- staturevision -->
	<xsl:template match="statuterevision">
		    <xsl:apply-templates/>
	  </xsl:template>

	  <!-- placeholdertext -->
	<xsl:template match="placeholdertext">
		    <xsl:apply-templates/>
	  </xsl:template>
	
	  <!-- reg:title -->
	<xsl:template match="*:title">
		    <xsl:apply-templates/>
	  </xsl:template>

	  <!-- chapter -->
	<xsl:template match="chapter">
		    <xsl:apply-templates/>
	  </xsl:template>

    <!-- yearenacted -->
	<xsl:template match="yearenacted">
		    <xsl:apply-templates/>
	  </xsl:template>
	
	  <!-- reg:defunct -->
	<xsl:template match="reg:defunct">
		    <xsl:apply-templates/>
	  </xsl:template>
	
	

	  <!-- ** *********Currency Table ****************
	In this section we define the currency table
	for the beginning of the page.
 -->
	<xsl:template match="currency">
		    <xsl:variable name="classtype">
			      <xsl:choose>
				        <xsl:when test="/descendant::ammend">
					          <xsl:text>currency</xsl:text>
				        </xsl:when>
				        <xsl:otherwise>
					          <xsl:choose>
						            <xsl:when test="/descendant::tlc">
							              <xsl:text>currency</xsl:text>
						            </xsl:when>
						            <xsl:otherwise>
							              <xsl:text>currencysingle</xsl:text>
						            </xsl:otherwise>
					          </xsl:choose>
				        </xsl:otherwise>
			      </xsl:choose>
		    </xsl:variable>

		    <!-- This must be changed in the future to reflect if we have
			ammended text and such!! -->

		<div id="actcurrency">
			      <table align="center" cellpadding="2" cellspacing="0">
				        <tr>
					          <xsl:element name="td">
						            <xsl:attribute name="colspan">
							              <xsl:text>4</xsl:text>
						            </xsl:attribute>
						            <xsl:attribute name="class">
							              <xsl:value-of select="$classtype"/>
						            </xsl:attribute>
						            <xsl:choose>
							              <xsl:when test="/descendant::currencydate">This Act is current to
									<xsl:value-of select="/descendant::currencydate"/>
                     </xsl:when>
							              <xsl:otherwise>
								                <xsl:choose>
									                  <xsl:when test="count(//content) &gt; 1">
										<!-- <img alt="Qp Date"
											src="https://styles.qp.gov.bc.ca/media/qpDate.gif"/>-->
										<xsl:if test="$dateFile">This Act is current to <xsl:value-of select="$dateFile/root/currency_date"/>
                              </xsl:if>
									                  </xsl:when>
									                  <xsl:otherwise>
										<!-- <img alt="Qp Date"
											src="https://styles.qp.gov.bc.ca/media/qpDate.gif"/>-->
										<xsl:if test="$dateFile">This Act is current to <xsl:value-of select="$dateFile/root/currency_date"/>
                              </xsl:if>
									                  </xsl:otherwise>
								                </xsl:choose>
							              </xsl:otherwise>
						            </xsl:choose>
					          </xsl:element>
				        </tr>
				        <xsl:if test="/descendant::ammendtext">
					          <tr>
						            <td class="tabletext" colspan="4">
							              <xsl:value-of select="/descendant::ammendtext"/>
						            </td>
					          </tr>
				        </xsl:if>
				        <xsl:if test="/descendant::ammend">
					          <tr>
						            <th>Effective Date</th>
						            <th>Section of Act<br/> Amended</th>
						            <th>Source of Change</th>
						            <th>Brought into<br/> Force by</th>
					          </tr>
				        </xsl:if>
				        <!-- Here because of the way preceding:: works (ie. even though
				it sorts the data, it still looks at the preceding element
				unsorted) we'll create a variable of our sorted lis) -->
				<xsl:for-each select="/descendant::ammend">
					          <xsl:choose>
						            <xsl:when test="source/sourcebill = following::ammend[1]/source/sourcebill">
							              <tr>
								                <td class="tabledatanorule">
									                  <xsl:value-of select="effectivedate"/>
								                </td>
								                <td class="tabledatanorule">
									                  <xsl:value-of select="sectionammended"/>
								                </td>
								                <td class="tabledatanorule">Bill <xsl:value-of select="source/sourcebill"/>, c. <xsl:value-of select="source/sourcechapter"/>, <xsl:value-of select="source/sourceyear"/>, <br/>s. <xsl:value-of select="source/sourcesection"/>
                        </td>
								                <td class="tabledatanorule">Reg <xsl:value-of select="inforce/reg:regulation"/>
									                  <br/>OIC <xsl:value-of select="inforce/reg:oic"/>
                        </td>
							              </tr>
						            </xsl:when>
						            <xsl:otherwise>
							              <xsl:choose>
								                <xsl:when test="position() = 1">
									                  <tr>
										                    <td class="tabledatanorule">
											                      <xsl:value-of select="effectivedate"/>
										                    </td>
										                    <td class="tabledatanorule">
											                      <xsl:value-of select="sectionammended"/>
										                    </td>
										                    <td class="tabledatanorule">Bill <xsl:value-of select="source/sourcebill"/>, c. <xsl:value-of select="source/sourcechapter"/>, <xsl:value-of select="source/sourceyear"/>, <br/>s. <xsl:value-of select="source/sourcesection"/>
                              </td>
										                    <td class="tabledatanorule">Reg <xsl:value-of select="inforce/reg"/>
											                      <br/>OIC <xsl:value-of select="inforce/reg:oic"/>
                              </td>
									                  </tr>
								                </xsl:when>
								                <xsl:otherwise>
									                  <tr>
										                    <td class="tabledatarule">
											                      <xsl:value-of select="effectivedate"/>
										                    </td>
										                    <td class="tabledatarule">
											                      <xsl:value-of select="sectionammended"/>
										                    </td>
										                    <td class="tabledatarule">Bill <xsl:value-of select="source/sourcebill"/>, c. <xsl:value-of select="source/sourcechapter"/>, <xsl:value-of select="source/sourceyear"/>, <br/>s. <xsl:value-of select="source/sourcesection"/>
                              </td>
										                    <td class="tabledatarule">Reg <xsl:value-of select="inforce/reg:regulation"/>
											                      <br/>OIC <xsl:value-of select="inforce/reg:oic"/>
                              </td>
									                  </tr>
								                </xsl:otherwise>
							              </xsl:choose>
						            </xsl:otherwise>
					          </xsl:choose>
				        </xsl:for-each>
				        <xsl:if test="/descendant::tlc">
					          <xsl:variable name="mytlc">
						            <xsl:value-of select="normalize-space(tlc/text())"/>
					          </xsl:variable>
					          <tr>
						            <td class="tabletext" colspan="4">This Act has "Not in Force" sections.
								<em>See</em> the <a href="#!-- #ID:{normalize-space(translate(tlc, ' ', ''))} --#">Table
								of Legislative Changes.</a>
                  </td>
					          </tr>
				        </xsl:if>
			      </table>
		    </div>
	  </xsl:template>




	  <!-- reg:content -->
	<xsl:template match="reg:content" mode="toc">
		    <xsl:apply-templates mode="toc"/>
	  </xsl:template>


	
	  <!-- preamble -->
	<!--<xsl:template match="preamble" mode="content">
		<div class="preamble">
			<xsl:if test="preamblehead">
				<h4>
					<xsl:apply-templates select="preamblehead"/>
				</h4>
			</xsl:if>
			<xsl:apply-templates/>
		</div>
	</xsl:template>


	<xsl:template match="preamblehead">
		<xsl:apply-templates/>
	</xsl:template>-->
	<!-- end of preamble -->




	<!--	<xsl:template match="a">
		<xsl:element name="a">
			<xsl:copy-of select="@*"/>
			<xsl:apply-templates/>
		</xsl:element>
	</xsl:template>
	<xsl:template match="hr">
		<xsl:element name="hr">
			<xsl:attribute name="noshade">noshade</xsl:attribute>
		</xsl:element>
		<xsl:apply-templates/>
	</xsl:template>-->

	<!--<xsl:template match="degree">
		<xsl:text disable-output-escaping="yes">°</xsl:text>
	</xsl:template>-->


	<!--	<xsl:template match="strikethrough">
		<span class="strikethrough">
			<xsl:apply-templates/>
		</span>
		</xsl:template>-->
	
	<!--	<xsl:template match="doubleunderline">
		<span class="doubleunderline">
			<xsl:apply-templates/>
		</span>
	</xsl:template>-->


<!-- I believe its time to take the following 6 elements out -->
	<xsl:template match="eacute">
		    <xsl:text disable-output-escaping="yes">é</xsl:text>
	  </xsl:template>
	
	
	  <xsl:template match="strong|em|u|sup|sub|br">
		    <xsl:element name="{name()}">
			      <xsl:apply-templates/>
		    </xsl:element>
	  </xsl:template>
	
	
	  <xsl:template match="insert">
		    <xsl:text disable-output-escaping="yes">&lt;insert&gt;</xsl:text>
		    <span class="insert">
			      <xsl:apply-templates/>
		    </span>
		    <xsl:text disable-output-escaping="yes">&lt;/insert&gt;</xsl:text>
	  </xsl:template>
	
	  <xsl:template match="red">
		    <span class="red">
			      <xsl:apply-templates/>
		    </span>
	  </xsl:template>
	
	  <xsl:template match="lt">
		    <xsl:text disable-output-escaping="yes">&lt;insert&gt;</xsl:text>
		    <span class="insert">
			      <xsl:apply-templates/>
		    </span>
		    <xsl:text disable-output-escaping="yes">&lt;/insert&gt;</xsl:text>
	  </xsl:template>
	
	  <xsl:template match="gt">
		    <xsl:text disable-output-escaping="yes">&gt;</xsl:text>
	  </xsl:template>

	  <!-- *********    Final Section   **************** 

 	This Section consits of templates for removing the 
	leading and trailing spaces from all our text node
	as well as removing all text from sections such
	as our Table of Contents -->

	<!--
	<xsl:template match="text()[preceding-sibling::node() and                             following-sibling::node()]">
		<xsl:variable name="ns" select="normalize-space(concat('x',.,'x'))"/>
		<xsl:value-of select="substring( $ns, 2, string-length($ns) - 2 )"/>
	</xsl:template>
	<xsl:template match="text()[preceding-sibling::node() and                             not( following-sibling::node() )]">
		<xsl:variable name="ns" select="normalize-space(concat('x',.))"/>
		<xsl:value-of select="substring( $ns, 2, string-length($ns) - 1 )"/>
	</xsl:template>
	<xsl:template match="text()[not( preceding-sibling::node() ) and                             following-sibling::node()]">
		<xsl:variable name="ns" select="normalize-space(concat(.,'x'))"/>
		<xsl:value-of select="substring( $ns, 1, string-length($ns) - 1 )"/>
	</xsl:template>
	<xsl:template match="text()[not( preceding-sibling::node() ) and                             not( following-sibling::node() )]">
		<xsl:value-of select="normalize-space(.)"/>
	</xsl:template> -->

	<!--<xsl:template match="text()" mode="currencyinfo"/>-->
	<!--<xsl:template match="text()" mode="toc"/>-->
	<!--	<xsl:template match="text()">
		<xsl:value-of select="."/>
	</xsl:template>-->
	<!--<xsl:template match="text()" mode="content"/>-->
	<!--<xsl:template match="text()" mode="contentsection"/>-->
	<!--<xsl:template match="text()" mode="indent1"/>-->
	<!-- ***********     Table Section      ***************

		In this section we deal with everything
		table!!
	-->
	<xsl:template match="ccollect">
		    <ccollect value="{@value}"/>
	  </xsl:template>


	

	  <xsl:template match="seealso_note"/>

	  <!-- NXT's Hit highlighting and TOC navigation -->
	<!--	<xsl:template match="lp-toc">
		<a name="LPTOC{@anchor}"/>
	</xsl:template>

	<xsl:template match="lp-hit">
		<span id="lphit" style="color:#006600; background: #CCFFCC">
			<xsl:apply-templates/>
		</span>
		<xsl:text> </xsl:text>
	</xsl:template>
	<xsl:template match="lp-hit-anchor">
		<a name="LPHit{@count}"/>
	</xsl:template>
	<xsl:template match="lp-hit-total">
		<form name="LPHitCountForm">
			<input name="LPHitCount" type="hidden" value="{@count}"/>
		</form>
	</xsl:template>-->


	<!-- reg:regnote -->
	<xsl:template match="reg:regnote|regnote">
		    <p class="regnote">
			      <xsl:apply-templates/>
		    </p> 
	  </xsl:template>



	  <!-- reg:provisionsnote -->
	<xsl:template match="reg:provisionsnote|provisionsnote">
		    <p class="provisionsnote">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>

	  <xsl:template match="*">
		    <div style="font-weight:bold; color:red;">
			      <xsl:text>Unmatched Element:</xsl:text>
			      <xsl:value-of select="name()"/>
		    </div>
	  </xsl:template>


	  <xsl:template match="reg:amend"/>


	  <xsl:template match="footref">
		    <a href="#footnote_{.}">
			      <sup>
				        <xsl:apply-templates/>
			      </sup>
		    </a>
	  </xsl:template>

	  <xsl:template match="actname">
		    <em>
			      <xsl:apply-templates/>
		    </em>
	  </xsl:template>

</xsl:stylesheet>
<!-- QP BOTTOM OF DOC.  PLEASE KEEP AT BOTTOM OF DOCUMENT. DO NOT REMOVE OR MODIFY -->