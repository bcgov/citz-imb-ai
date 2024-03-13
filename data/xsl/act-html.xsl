<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:oasis="http://docs.oasis-open.org/ns/oasis-exchange/table"
                xmlns:ms="urn:schemas-microsoft-com:xslt"
                xmlns:act="http://www.gov.bc.ca/2013/legislation/act"
                xmlns:reg="http://www.gov.bc.ca/2013/legislation/regulation"
                xmlns:bcl="http://www.gov.bc.ca/2013/bclegislation"
                xmlns="http://www.w3.org/1999/xhtml"
                xmlns:in="http://www.qp.gov.bc.ca/2013/inline"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                exclude-result-prefixes="xsl ms"
                id="ACT-HTML_1.0.xsl"
                version="2.0">
	 
	  <xsl:strip-space elements="*"/>
	
	  <!-- Import common BC Legislation Elements -->
	<!-- test for file -->
	
	<!-- make sure this is the line pushed up the stack -->
	<xsl:include href="http://standards.qp.gov.bc.ca/standards/BCLEG-HTML.xsl"/>
	  <xsl:include href="http://standards.qp.gov.bc.ca/standards/DocNav.xsl"/>
	
	  <!--<xsl:param name="doinsert">true</xsl:param>-->
	<!--<xsl:param name="isTestContent" select="'false'"/>-->
	<!--<xsl:param name="aspect" select="'complete'"/>
	<xsl:param name="index" select="'statreg'"/>-->
	
	<!-- globalLink -->
	<xsl:variable select="'civix'" name="app"/>
	  <!--<xsl:variable name="aspect" select="'complete'"/>
	<xsl:variable name="index" select="'statreg'"/>-->
	<xsl:variable select="document('https://styles.qp.gov.bc.ca/media/qpDate.xml')"
                 name="dateFile"/>
	


	  <xsl:output doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN"
               indent="no"
               encoding="UTF-8"
               method="xhtml"/>
	  <!--<xsl:output doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN"	doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd" method="html"/>-->
	<xsl:strip-space elements="tlc"/>
	  <!-- **************************** VERSION 4.72 **************************** -->
	<!-- Changed MarginalNote template to look backwards as well as forwards for the sectionnumber
			in order to make the toc link work -->
	<!-- ****************************** VERSION ****************************** -->

	<xsl:template match="act:act">

		    <xsl:choose>
			<!-- Here we determine wether we have a multiple
		page document, or not. We do this by counting the
		occurences or "content". Any more than 1, we assume
		it's a multipy page document -->
			
			<!--Create a one file multi-->
			<xsl:when test="count(act:content) &gt; 1 and (contains(@id, '_multi') or $isTestContent = 'true')">
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
						            <xsl:value-of select="/act:act/@id"/>
					          </xsl:attribute>
					          <xsl:attribute name="isTestContent">
						            <xsl:value-of select="$isTestContent"/>
					          </xsl:attribute>
					          <head>
						            <META content="text/html; charset=utf-8" http-equiv="Content-Type"/>
						            <!-- Emulate IE7 -->
						<!--<META content="IE=8" http-equiv="X-UA-Compatible"/>-->
						<META content="IE=edge" http-equiv="X-UA-Compatible"/>
						            <title>Full Multi - <xsl:value-of select="act:title"/>
                  </title>
						
						            <!-- css -->
						<link href="/standards/Acts.css" rel="stylesheet" type="text/css"/>
						            <!-- /css -->
						<script src="https://code.jquery.com/jquery-1.7.1.min.js"
                          type="text/javascript"/>
						            <xsl:choose>
							              <xsl:when test="$isSearchResult">
                        <script src="/standards/hitNav.js" type="text/javascript"/>
                     </xsl:when>
						            </xsl:choose>
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
						            <xsl:apply-templates select="ccollect"/>
						
					          </head>
					          <body bgcolor="#FFFFFF" text="#000000">
						            <xsl:call-template name="topBanner"/>
						            <div id="contentsscroll">
							<!-- <xsl:call-template name="divStart"/> -->
							<xsl:call-template name="htmHeaderAct"/>
							              <xsl:call-template name="htmTableContentsBCL"/>
							              <xsl:apply-templates select="act:content"/>
							              <xsl:apply-templates select="bcl:multinav"/>
							              <p class="copyright">Copyright © King's Printer, Victoria, British
								Columbia, Canada</p>
							              <!-- <xsl:call-template name="divEnd"/> -->
						</div>
					          </body>
				        </xsl:element>
			      </xsl:when>

			      <xsl:when test="count(act:content) &gt; 1">
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
						            <xsl:value-of select="/act:act/@id"/>
					          </xsl:attribute>
					          <xsl:attribute name="isTestContent">
						            <xsl:value-of select="$isTestContent"/>
					          </xsl:attribute>
					          <head>
						            <META content="text/html; charset=utf-8" http-equiv="Content-Type"/>
						
						            <META content="IE=edge" http-equiv="X-UA-Compatible"/>
						            <title>Table of Contents - <xsl:value-of select="act:title"/>
                  </title>

						            <!-- css -->
						<link href="/standards/Acts.css" rel="stylesheet" type="text/css"/>
						            <!-- /css -->
						<script src="https://code.jquery.com/jquery-1.7.1.min.js"
                          type="text/javascript"/>
						            <xsl:choose>
							              <xsl:when test="$isSearchResult">
                        <script src="/standards/hitNav.js" type="text/javascript"/>
                     </xsl:when>

						            </xsl:choose>
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
						            <xsl:apply-templates select="ccollect"/>

					          </head>
					          <body bgcolor="#FFFFFF" text="#000000">
						            <xsl:call-template name="topBanner"/>
						            <div id="contentsscroll">
						<!-- <xsl:call-template name="divStart"/> -->
						<xsl:call-template name="htmHeaderAct"/>
						               <xsl:call-template name="htmTableContentsBCL"/>

						               <p class="copyright">Copyright © King's Printer, Victoria, British
							Columbia, Canada</p>
							              <!-- <xsl:call-template name="divEnd"/> -->
						</div>
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
					          <xsl:attribute name="isTestContent">
						            <xsl:value-of select="$isTestContent"/>
					          </xsl:attribute>
					          <head>
						            <META content="text/html; charset=utf-8" http-equiv="Content-Type"/>
						
						            <META content="IE=edge" http-equiv="X-UA-Compatible"/>

						            <title>
							              <xsl:value-of select="act:title"/>
						            </title>

						            <xsl:choose>
							              <xsl:when test="/act:act/attribute::notoc">
								<!-- css -->
								<link href="/standards/Acts.css" rel="stylesheet" type="text/css"/>
								                <!-- /css -->
							</xsl:when>
							              <xsl:otherwise>
								                <xsl:choose>
									                  <xsl:when test="/act:act/supplement">
										<!-- css -->
										<link href="/standards/Acts.css" rel="stylesheet" type="text/css"/>
										                    <!-- /css -->
									</xsl:when>
									                  <xsl:otherwise>
										<!-- css -->
										<link href="/standards/Acts.css" rel="stylesheet" type="text/css"/>
										                    <!-- /css -->
									</xsl:otherwise>
								                </xsl:choose>
							              </xsl:otherwise>
						            </xsl:choose>
						            <script src="https://code.jquery.com/jquery-1.7.1.min.js"
                          type="text/javascript"/>
						            <xsl:choose>
							              <xsl:when test="$isSearchResult">
                        <script src="/standards/hitNav.js" type="text/javascript"/>
                     </xsl:when>
						            </xsl:choose>
						
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
						            <!-- TODO: Review this, a test for hovering 
								If good must add to multi docs, regs and snippets. Also
								see xlink:href -->
						<style type="text/css">
							span.container {
								position:relative;
							}
	
							span.box {
								display:none;
							}

							a:hover+span.box, span.box iframe:hover, span.box:hover {
								display:block;
								z-index:100;
								position:absolute;
								left:10px;
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
						<!--<xsl:if test="//insert[1]">
							<h3>Geen text in this document</h3>
						</xsl:if>-->
						<xsl:call-template name="topBanner"/>
						            <!-- <xsl:call-template name="divStart"/> -->
						<div id="contentsscroll">
						               <xsl:call-template name="htmHeaderAct"/>
						               <xsl:if test="not(/act:act/attribute::notoc)">
							                 <xsl:call-template name="htmTableContentsBCL"/>
						               </xsl:if>
						               <xsl:apply-templates select="act:content"/>
						               <xsl:apply-templates select="bcl:multinav"/>

						               <p class="copyright">Copyright © King's Printer, Victoria, British
							Columbia, Canada</p>
						            </div>
						            <!-- <xsl:call-template name="divEnd"/> -->
					</body>
				        </xsl:element>
			      </xsl:otherwise>
		    </xsl:choose>
	  </xsl:template>

	  <xsl:template match="act:preamble">
		    <div class="preamble">
			      <xsl:apply-templates/>
		    </div>	
	  </xsl:template>
	
	  <xsl:template match="act:preamble/act:text">
		    <p>
         <xsl:apply-templates/>
      </p>
	  </xsl:template>


	  <!-- Here we have the template that spits out our header text -->
	<xsl:template name="htmHeaderAct">

		    <xsl:if test="not(ancestor::change)">
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
		    </xsl:if>
		
		    <!--add link to the full multi-->
		<xsl:if test="@isMulti and not(contains(@id, '_multi'))">
			      <xsl:variable name="oneFileMulti">
				        <xsl:value-of select="concat('/', $app, '/document/id/', $aspect, '/', $index, '/', replace(@index,'_multi','_00_multi'))"/>
			      </xsl:variable>
			      <p align="right" class="bold">
            <a href="{$oneFileMulti}">View Complete Statute</a>
         </p>
		    </xsl:if>
		
		    <xsl:variable name="classtype">
			      <xsl:choose>
				        <xsl:when test="act:tlc">currency</xsl:when>
				        <xsl:otherwise>currencysingle</xsl:otherwise>
			      </xsl:choose>
		    </xsl:variable>

		    <!-- This must be changed in the future to reflect if we have
			ammended text and such!! -->

		<xsl:if test="not(ancestor::change)">
			      <xsl:choose>
				        <xsl:when test="act:currency/@noCurrencyDate='true'"/> 
            <!-- Do not display a currency date for federal statues -->
				<xsl:otherwise>
					          <div id="act:currency">
						            <table align="center" cellpadding="2" cellspacing="0">
							              <tr>
								                <td class="{$classtype}" colspan="4">
									                  <xsl:choose>
										
										                    <xsl:when test="act:currency/act:currencydate">This Act is current to
											<xsl:value-of select="act:currency/act:currencydate"/>
                              </xsl:when>
										                    <xsl:otherwise>
										                       <xsl:if test="$dateFile">
											This Act is current to <xsl:value-of select="$dateFile/root/currency_date"/>
                                 </xsl:if>
											                      <!-- <img alt="Qp Date" src="https://styles.qp.gov.bc.ca/media/qpDate.gif"/>-->
											<!--</xsl:otherwise>
							</xsl:choose>-->
										</xsl:otherwise>
									                  </xsl:choose>
								                </td>
							              </tr>
							              <!-- added to deal with the rules of court tlc issues -->
							<xsl:choose>
								                <xsl:when test="not(//act:currency[1]/@notlc)">
									                  <xsl:if test="$doinsert = 'true'">
										                    <xsl:apply-templates select="act:currency"/>
									                  </xsl:if>
								                </xsl:when>
							              </xsl:choose>
						            </table>
					          </div>
				        </xsl:otherwise>
			      </xsl:choose>
		    </xsl:if>
		    <xsl:apply-templates select="/act:act/act:conveniencehead|/act:act/act:prerevisednote|/act:act/supplement"/>
		    <div id="title">
			      <xsl:apply-templates select="act:title"/>
			      <xsl:if test="act:statuterevision">
				        <p align="center" class="bold">
					          <xsl:apply-templates select="act:statuterevision"/>
				        </p>
			      </xsl:if>
			      <xsl:choose>
				        <xsl:when test="not($doinsert = 'true')">
					          <xsl:if test="act:yearenacted">
						            <h3>
							              <xsl:choose>
								                <xsl:when test="act:yearenacted/@revised='RSBC'">[RSBC </xsl:when>
								                <xsl:when test="act:yearenacted/@revised='RSC'">[RSC </xsl:when>
								                <xsl:when test="act:yearenacted/@revised='SBC'">[SBC </xsl:when>
								                <xsl:when test="act:yearenacted/@prefix">[<xsl:value-of select="act:yearenacted/@prefix"/>
                           <xsl:text> </xsl:text>
                        </xsl:when>
								                <xsl:when test="act:yearenacted='1996'">[RSBC<xsl:text> </xsl:text>
                        </xsl:when>
								                <xsl:when test="act:yearenacted='1960'">[RSBC<xsl:text> </xsl:text>
                        </xsl:when>
								                <xsl:when test="act:yearenacted='1996 (Supp)'">[RSBC<xsl:text> </xsl:text>
                        </xsl:when>
								                <xsl:otherwise>[SBC<xsl:text> </xsl:text>
                        </xsl:otherwise>
							              </xsl:choose>
							              <xsl:apply-templates select="act:yearenacted"/>] CHAPTER
								<xsl:apply-templates select="act:chapter"/>
						            </h3>
					          </xsl:if>
				        </xsl:when>
				        <xsl:when test="act:placeholderlink">
					          <xsl:variable select="act:placeholderlink" name="idlinktestt"/>
					          <a href="/civix/document/id/psl/psl/{$idlinktestt}">
					<!--<a href="/nxt/gateway.dll?f=id$id={$idlinktestt}$t=document-frame.htm$3.0">-->
						<h3>
							              <xsl:choose>
								                <xsl:when test="act:yearenacted/@revised='RSBC'">[RSBC </xsl:when>
								                <xsl:when test="act:yearenacted/@revised='RSC'">[RSC </xsl:when>
								                <xsl:when test="act:yearenacted/@revised='SBC'">[SBC </xsl:when>
								                <xsl:when test="act:yearenacted/@prefix">[<xsl:value-of select="act:yearenacted/@prefix"/>
                           <xsl:text> </xsl:text>
                        </xsl:when>
								                <xsl:when test="act:yearenacted='1996'">[RSBC<xsl:text> </xsl:text>
                        </xsl:when>
								                <xsl:when test="act:yearenacted='1960'">[RSBC<xsl:text> </xsl:text>
                        </xsl:when>
								                <xsl:when test="act:yearenacted='1996 (Supp)'">[RSBC<xsl:text> </xsl:text>
                        </xsl:when>
								                <xsl:otherwise>[SBC<xsl:text> </xsl:text>
                        </xsl:otherwise>
							              </xsl:choose>
							              <xsl:apply-templates select="/act:act/act:yearenacted"/>] CHAPTER
								<xsl:apply-templates select="act:chapter"/>
						            </h3>
					          </a>
				        </xsl:when>
				        <xsl:otherwise>
					          <xsl:if test="act:yearenacted">
						            <h3>
							              <xsl:choose>
								                <xsl:when test="act:yearenacted/@revised='RSBC'">[RSBC </xsl:when>
								                <xsl:when test="act:yearenacted/@revised='RSC'">[RSC </xsl:when>
								                <xsl:when test="act:yearenacted/@revised='SBC'">[SBC </xsl:when>
								                <xsl:when test="act:yearenacted/@prefix">[<xsl:value-of select="act:yearenacted/@prefix"/>
                           <xsl:text> </xsl:text>
                        </xsl:when>
								                <xsl:when test="act:yearenacted='1996'">[RSBC<xsl:text> </xsl:text>
                        </xsl:when>
								                <xsl:when test="act:yearenacted='1960'">[RSBC<xsl:text> </xsl:text>
                        </xsl:when>
								                <xsl:when test="act:yearenacted='1996 (Supp)'">[RSBC<xsl:text> </xsl:text>
                        </xsl:when>
								                <xsl:otherwise>[SBC<xsl:text> </xsl:text>
                        </xsl:otherwise>
							              </xsl:choose>
							              <xsl:apply-templates select="act:yearenacted"/>] CHAPTER
								<xsl:apply-templates select="act:chapter"/>
						            </h3>
					          </xsl:if>
				        </xsl:otherwise>
			      </xsl:choose>
			      <xsl:apply-templates select="act:deposited|act:repealedtext"/>
		    </div>
	  </xsl:template>


   <!-- act:supplement -->
	<xsl:template match="act:supplement">
		    <p align="center">
			      <strong>
				        <em>
					          <xsl:apply-templates/>
				        </em>
			      </strong>
		    </p>
	  </xsl:template>

	  <!-- act:title -->
	<xsl:template match="act:title">
		    <h2>
			      <xsl:apply-templates/>
		    </h2>
	  </xsl:template>

	  <xsl:template match="act:statuterevision">
		    <p align="center" class="bold">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>

	  <!-- act:conveniencehead -->
	<xsl:template match="act:conveniencehead">
		    <p align="center">
			      <em>
				        <xsl:apply-templates/>
			      </em>
		    </p>
	  </xsl:template>


	  <!--<xsl:template match="*" mode="toc"/>-->

	<!-- act:content -->
	<xsl:template match="act:content" mode="toc">
		    <xsl:apply-templates mode="toc"/>
	  </xsl:template>

	  <!-- act:assentedto -->
	<xsl:template match="act:assentedto">
		    <p align="right">
			      <em>Assented to <xsl:value-of select="."/>
         </em>
		    </p> 
	  </xsl:template>

	  <!-- act:deposited -->
	<xsl:template match="act:deposited">
		    <p align="right">
         <em>
			         <xsl:apply-templates/>
		       </em>
      </p>
	  </xsl:template>

	  <!-- act:chapter -->
	<xsl:template match="act:chapter">
		    <xsl:apply-templates/>
	  </xsl:template>
	
	  <!-- reg:prerevisednote -->
	<xsl:template match="act:prerevisednote">
		    <p class="prnote">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>

	  <!-- act:yearenacted  -->
	<xsl:template match="act:yearenacted">
		    <xsl:apply-templates/>
	  </xsl:template>
	  <!-- ******************* End Of Template **************** -->
	<!-- This is the end of the HTML and beginning
	of the templates
 -->
	<!-- ** *********Currency Table ****************
	In this section we define the currency table
	for the beginning of the page.
 -->
	<xsl:template match="act:currency">
		<!-- This choose block is creating the TLC link.  It is either a link to a TLC doc, or to the TLC folder.  Wording is slightly different in each case -->
		<xsl:choose>
			<!-- This element means that we should point to a dir -->
			<xsl:when test="act:tlcDirPath">
				<!-- This is how the two differnt links will look. -->
				<!--/civix/document/id/complete/statreg/E2tlc96385
				/civix/content/complete/statreg/524872423/96005/tlc96005_f/?xsl=/templates/browse.xsl-->
				
				<!-- ensuring the slashes go the right direction -->
				<xsl:variable name="slashCorrectedTLCDirPath">
					          <xsl:value-of select="translate(act:tlcDirPath, '\\', '/')"/>
				        </xsl:variable>
				
				        <!-- Ensureing we have both a leading and trailing slash in the tlcDirPath element -->
				<xsl:variable name="tlcDirPathFrontSlash">
					          <xsl:choose>
						            <xsl:when test="not(starts-with($slashCorrectedTLCDirPath, '/'))">
							              <xsl:value-of select="concat('/', act:tlcDirPath)"/>
						            </xsl:when>
						            <xsl:otherwise>
							              <xsl:value-of select="$slashCorrectedTLCDirPath"/>
						            </xsl:otherwise>
					          </xsl:choose>
				        </xsl:variable>
				        <xsl:variable name="cleanedTLCDirPath">
					          <xsl:choose>
						            <xsl:when test="not(ends-with($tlcDirPathFrontSlash, '/'))">
							              <xsl:value-of select="concat($tlcDirPathFrontSlash, '/')"/>
						            </xsl:when>
						            <xsl:otherwise>
							              <xsl:value-of select="$tlcDirPathFrontSlash"/>
						            </xsl:otherwise>
					          </xsl:choose>
				        </xsl:variable>
				
				        <!-- Building the full link -->
				<xsl:variable name="tlclink">
					          <xsl:choose>
												<xsl:when test="$aspect = 'roc'">
							              <xsl:value-of select="concat('/', $app, '/content/complete/statreg', translate(normalize-space($cleanedTLCDirPath), ' ', ''), '?xsl=/templates/browse.xsl')"/>
						            </xsl:when>
						            <xsl:otherwise>
							              <xsl:value-of select="concat('/', $app, '/content/', $aspect, '/', $index, translate(normalize-space($cleanedTLCDirPath), ' ', ''), '?xsl=/templates/browse.xsl')"/>
						            </xsl:otherwise>
					          </xsl:choose>
				        </xsl:variable>
								
				        <tr>
					          <td class="tabletext" colspan="4">See the <a href="{$tlclink}">Tables of Legislative Changes</a> for this Act’s legislative history, including any changes not in force.</td>
				        </tr>
			      </xsl:when>
			
			      <!-- This element means we point to a specific TLC document -->
			<xsl:when test="act:tlc">
				
				<!--Building the full link -->
				<xsl:variable name="tlclink">
					          <xsl:value-of select="concat('/', $app, '/document/id/', $aspect, '/', $index, '/', translate(normalize-space(act:tlc), ' ', ''))"/>
				        </xsl:variable>
				        <tr>
					          <td class="tabletext" colspan="4">See the <a href="{$tlclink}">Table of Legislative Changes</a> for this Act’s recent legislative history, including any changes not in force.</td>
				        </tr>
			      </xsl:when>
		    </xsl:choose>
		    <!-- 
		<xsl:variable name="file">
			<xsl:value-of select="translate(normalize-space(.), ' ', '')"/>
		</xsl:variable>-->
		<!--<xsl:if test="not(exists('/nxt/gateway.dll?f=id$id={$file}$t=document-frame.htm$3.0'))">-->
		
		<!--</xsl:if>-->
	</xsl:template>
	  <xsl:template match="act:tlc"/>
	  <xsl:template match="act:tlcDirPath" mode="#all"/>

	  <!-- ************** Content ********************
		In this section we define the templates that
		will determine the look of the content after
		the table of contents -->

	<xsl:template match="act:content">
		    <xsl:apply-templates/>
	  </xsl:template>


	  <!-- act:Repealed -->
		<xsl:template match="act:repealedtext">
		    <p align="center" field="repealedtext">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>
	  <!-- End of repealed -->


	<!-- heading -->
	<xsl:template match="heading">
		    <p align="center" class="bold">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>


	  <!-- Here are our inline tags -->


	<xsl:template match="desc">
		    <em>
			      <xsl:apply-templates/>
		    </em>
	  </xsl:template>






	  <xsl:template match="actname">
		    <em>
			      <xsl:apply-templates/>
		    </em>
	  </xsl:template>

   <!--	<xsl:template match="insert">
		<xsl:choose>
			<xsl:when test="$doinsert = 'true'">
				<insert>
					<span class="insert">
						<xsl:apply-templates/>
					</span>
				</insert>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>-->

	<xsl:template match="ccollect">
		    <ccollect value="{@value}"/>
	  </xsl:template>





	  <xsl:template match="*">
		    <div style="font-weight:bold; color:red;">
			      <xsl:text>Unmatched Element:</xsl:text>
			      <xsl:value-of select="name()"/>
		    </div>
	  </xsl:template>


</xsl:stylesheet>
<!-- QP BOTTOM OF DOC.  PLEASE KEEP AT BOTTOM OF DOCUMENT. DO NOT REMOVE OR MODIFY -->
