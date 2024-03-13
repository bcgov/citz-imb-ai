<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:byl="http://www.gov.bc.ca/2015/bylaw"
                xmlns:bcl="http://www.gov.bc.ca/2013/bclegislation"
                xmlns:in="http://www.qp.gov.bc.ca/2013/inline"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                xmlns:oasis="http://docs.oasis-open.org/ns/oasis-exchange/table"
                xmlns:act="http://www.gov.bc.ca/2013/legislation/act"
                xmlns:reg="http://www.gov.bc.ca/2013/legislation/reg"
                xmlns:amd="http://www.gov.bc.ca/2017/amendment"
                version="2.0"
                exclude-result-prefixes="xs">

	  <xsl:include href="/standards/BCLEG-HTML.xsl"/>
	  <xsl:include href="/standards/DocNav.xsl"/>
	  <xsl:output doctype-public="-//W3C//DTD HTML 4.0 Transitional//EN"
               doctype-system="http://www.w3.org/TR/html4/loose.dtd"
               encoding="UTF-8"
               indent="no"
               method="xhtml"/>
	
	  <!-- ****************************** -->
		<!-- Bylaw. -->
	<!-- ****************************** -->

	<xsl:template match="*:bylaw">

		<!-- TODO: Auto-generated template -->
		<div id="actname">
			      <xsl:apply-templates select="byl:bylawno"/>
		    </div>
		    <div id="title">
			      <xsl:apply-templates select="byl:title | byl:longtitle"/>
		    </div>
		    <div id="amsincluded">
			      <xsl:apply-templates select="byl:amsincluded"/>
		    </div>
		    <xsl:if test="not(byl:content[@toc ='false'])">
			      <xsl:call-template name="htmTableContentsBYL"/>
		    </xsl:if>
		    <xsl:apply-templates select="byl:content"/>
	  </xsl:template>
	
	  <!-- Table of Contents BYL -->
	<xsl:template name="htmTableContentsBYL">
		
		    <xsl:if test="not(repealedtext) and not(placeholderlink)">
			<!-- to do add away to stop notice.xmls to have the word content to appear -->
			<xsl:if test="not(//reg:NIF)">
				        <xsl:if test="//bcl:section[1] or //bcl:subrule[1]">
					          <xsl:choose>
						            <xsl:when test="not(//bcl:section[1])">
							              <div id="contents">
								                <table border="0" cellpadding="3" cellspacing="0">
									                  <tr>
										                    <th colspan="3">
											                      <em>Contents</em>
										                    </th>
									                  </tr>
									                  <!--<xsl:apply-templates mode="byl_toc"/>-->
								</table>
							              </div>
						            </xsl:when>
						            <xsl:when test="not(//bcl:section/@toc = 'false')">
							              <div id="contents">
								                <table border="0" cellpadding="3" cellspacing="0">
									                  <tr>
										                    <th colspan="3">
											                      <em>Contents</em>
										                    </th>
									                  </tr>
									                  <xsl:apply-templates mode="byl_toc"/>
								                </table>
							              </div>
						            </xsl:when>
					          </xsl:choose>
				        </xsl:if>
			      </xsl:if>
		    </xsl:if>
	  </xsl:template>
	
	  <!-- Exclude unwanted text output in TOC  -->
	<xsl:template match="text()" mode="byl_toc"/>
	
	  <!-- Exclude amending sections and their children from TOC -->
	<xsl:template match="amd:section/*" mode="byl_toc"/>
	
	  <!-- bcl:part BYL TOC -->
	<xsl:template match="bcl:part" mode="byl_toc">
		    <xsl:variable name="idtag1">
			      <xsl:value-of select="concat('#part', bcl:num)"/>
		    </xsl:variable>
		    <tr>
			      <td align="left" class="part" colspan="3" valign="top">
				        <xsl:element name="a">
					          <xsl:attribute name="href">
						            <xsl:value-of select="normalize-space($idtag1)"/>
					          </xsl:attribute>Part <xsl:apply-templates select="bcl:num"/>
					          <xsl:if test="bcl:text"> — <xsl:apply-templates select="bcl:text"/>
               </xsl:if>
				        </xsl:element>
			      </td>
		    </tr>	
		    <xsl:apply-templates mode="byl_toc"/>
	  </xsl:template>
	
	  <!-- bcl:section BYL TOC -->
	<xsl:template match="bcl:section" mode="byl_toc">
		    <xsl:if test="not(@toc = 'false') and ./bcl:marginalnote">
			
			      <xsl:variable name="idtag">
				        <xsl:value-of select="concat('#section', bcl:num)"/>
			      </xsl:variable>
			      <tr>
				        <td align="left"> </td>
				        <td align="right" valign="top" width="10"> </td>
				        <td align="left" valign="top">
					
					          <a href="{$idtag}">
						            <xsl:value-of select="concat(normalize-space(bcl:num), ' ', bcl:marginalnote)"/>
					          </a>
				        </td>
			      </tr>
			
		    </xsl:if>		
	  </xsl:template>
	
	  <!-- bcl:division BYL TOC -->
	<xsl:template match="bcl:division" mode="byl_toc">
		    <xsl:variable name="idtag">#division_<xsl:value-of select="@id"/>
      </xsl:variable>
		    <tr>
			      <td align="left">
            <xsl:text> </xsl:text>
         </td>
			      <td align="left" class="division" colspan="2" valign="top">
				        <a href="{$idtag}">
					          <xsl:if test="bcl:num">Division <xsl:apply-templates select="bcl:num"/>
					          </xsl:if>
					          <xsl:if test="bcl:text">
						            <xsl:if test="bcl:num"> —<xsl:text> </xsl:text>
                  </xsl:if>
						            <xsl:apply-templates select="bcl:text"/>
					          </xsl:if>
				        </a>
			      </td>
			      <xsl:apply-templates mode="byl_toc"
                              select="bcl:section|bcl:conseqhead|bcl:schedule|bcl:rule|bcl:subrule|bcl:part"/>
		    </tr>
	  </xsl:template>
	
	  <!-- bcl:schedule BYL TOC -->
	<xsl:template match="bcl:schedule" mode="byl_toc">
		
		    <xsl:variable name="idtag">#<xsl:value-of select="translate(normalize-space(bcl:scheduletitle), ' ','')"/>
		    </xsl:variable>
		    <tr>
			      <td align="left" class="part" colspan="3" valign="top">
				        <a href="{$idtag}">
					          <xsl:value-of select="bcl:scheduletitle"/>
				        </a>
			      </td>
		    </tr>
		
	  </xsl:template>
	
	
	  <!-- bcl:conseqhead BYL TOC -->
	<xsl:template match="bcl:conseqhead" mode="byl_toc">
		    <xsl:variable name="idtag">
			      <xsl:if test="bcl:num">#section<xsl:value-of select="translate(normalize-space(translate(bcl:num, '-', 'to')), ' ','')"/>
			      </xsl:if>
		    </xsl:variable>
		    <tr>
			      <td align="right" valign="top" width="10">
            <xsl:text> </xsl:text>
         </td>
			      <td align="right" valign="top">
				        <xsl:element name="a">
					          <xsl:attribute name="href">
						            <xsl:value-of select="$idtag"/>
					          </xsl:attribute>
					          <xsl:apply-templates select="bcl:num" mode="noBrackets"/>
               <xsl:text> </xsl:text>
            </xsl:element>
			      </td>
			      <td valign="top">
				        <xsl:element name="a">
					          <xsl:attribute name="href">
						            <xsl:value-of select="$idtag"/>
					          </xsl:attribute>
					          <xsl:apply-templates select="bcl:text"/>
				        </xsl:element>
			      </td>
		    </tr>
	  </xsl:template>
	
	  <!-- bcl:link BYL TOC -->
	<!-- this is created to surpress the link function from the TOC -->
	<xsl:template match="bcl:link" mode="byl_toc">
		    <xsl:apply-templates/>
	  </xsl:template>
	
	  <!-- bcl:subsection/bcl:num made for BYL TOC -->
	<xsl:template match="bcl:subsection/bcl:num" mode="byl_toc">(<xsl:apply-templates/>)<xsl:text> </xsl:text>
   </xsl:template>
	
	
	  <xsl:template match="byl:bylawno">
		    <p align="center" class="bold">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>
	  <xsl:template match="byl:title">
		    <h2>
			      <xsl:apply-templates/>
		    </h2>
	  </xsl:template>
	  <xsl:template match="byl:amsincluded">
		    <p>
         <xsl:apply-templates/>
      </p>
	  </xsl:template>
	  <xsl:template match="byl:day">
		    <span class="day">
         <xsl:apply-templates/>,</span>
	  </xsl:template>
	  <xsl:template match="byl:preamble">
		    <div class="preamble">
			      <xsl:apply-templates select="byl:preambletext | bcl:paragraph"/>
		    </div>
	  </xsl:template>
	
	  <xsl:template match="byl:preambletext">
		    <p>
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>
	
	  <xsl:template match="byl:longtitle">
		    <p class="byl_lt">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>
	
	  <!--<xsl:template match="bcl:paragraph"><xsl:apply-templates select="bcl:paragraph"/></xsl:template> -->
	<xsl:template match="amd:lawnamehead">
		    <div class="amd_lawnamehead">
         <h4>
            <xsl:apply-templates/>
         </h4>
      </div>
	  </xsl:template>
	
	  <xsl:template match="amd:section/bcl:text[not(position() = 1)]">
		    <p class="amd-sec sandwich">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>
	  <!-- bcl:section/bcl:num -->
	<xsl:template match="amd:section/bcl:num">
		    <span class="amd-secnum">
			      <span class="amd-secnumholder">
			         <b>
				           <xsl:apply-templates/>
			         </b>
		       </span>
      </span>  </xsl:template>	
	  <!-- bcl:section -->
	<xsl:template match="amd:section">
		<!-- First we declare our href variable, due to some unfortunate whitespace issues -->
		<div class="section amd">
			      <a name="section{translate((normalize-space(translate(bcl:num, '-', 'to'))), ' ','')}"/>
			      <xsl:apply-templates select="bcl:marginalnote | bcl:transitionalhead"/>
			
				     <!--<xsl:attribute name="class">
					<xsl:choose>
						<xsl:when test="contains(bcl:num, '.')">
							<xsl:value-of
								select="concat('sec', string-length(normalize-space(translate(bcl:num, ' ', ''))) - 2, 'd1')"
							/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of
								select="concat('sec', string-length(normalize-space(translate(bcl:num, ' ', ''))))"
							/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:attribute>-->
				<!-- this was the og content -->
				
				<xsl:choose>
					       <xsl:when test="bcl:text[parent::amd:section]">
						         <p id="{@id}" class="amd-sec">
							           <xsl:apply-templates select="bcl:num[1]"/>
							           <xsl:apply-templates select="bcl:text[1]"/>
						         </p>
						         <p class="sub">
							           <a name="{bcl:subsection[1]/@id}"/>
							           <span class="num">
                     <span class="holder">
                        <xsl:apply-templates select="bcl:subsection[1]/bcl:num[1]"/>
                     </span>
                  </span>
							           <xsl:apply-templates select="bcl:subsection[1]/bcl:text[1]"/>
						         </p>
					       </xsl:when>
					       <xsl:otherwise>
						         <p id="{@id}" class="amd-sec">
							           <xsl:apply-templates select="bcl:num[1]"/>
							           <a name="{bcl:subsection/@id}"/>
							           <xsl:apply-templates select="bcl:subsection[1]/bcl:num"/>
							           <xsl:apply-templates select="bcl:subsection[1]/bcl:text[1]"/>
						         </p>
					       </xsl:otherwise>
				     </xsl:choose>
			
			      <xsl:apply-templates select="*[not(self::bcl:num[not(preceding-sibling::bcl:num)]) and not(self::bcl:text[not(preceding-sibling::bcl:text)]) and not(self::bcl:marginalnote) and not(self::bcl:transitionalhead)]"/>
		    </div>
	  </xsl:template>
	
	  <!-- bcl:paragraph -->
	<xsl:template match="amd:paragraph">
		    <xsl:choose>
			      <xsl:when test="(bcl:num[1])">
				        <p class="amd-para">
               <a name="{@id}"/>
					          <span class="amd-num">
                  <span class="amd-holder">(<xsl:apply-templates select="bcl:num"/>)</span>
               </span>
						         <xsl:apply-templates select="bcl:text[1]"/>
            </p>
			      </xsl:when>
			      <xsl:otherwise>
				        <p class="amd-para">
					          <a name="{@id}"/>
					          <xsl:apply-templates select="bcl:text[1]"/>
				        </p>
			      </xsl:otherwise>
		    </xsl:choose>
		    <xsl:apply-templates select="*[not(self::bcl:num) and not(self::bcl:text[not(preceding-sibling::bcl:text)])]"/>
	  </xsl:template>
	  <xsl:template match="amd:paragraph/bcl:paragraph">
		    <xsl:choose>
			      <xsl:when test="(bcl:num[1])">
				        <p class=" amd para">
               <a name="{@id}"/>
				           <span class="num">
                  <span class="holder">(<xsl:apply-templates select="bcl:num"/>)</span>
               </span>
			            <xsl:text> </xsl:text>
			            <xsl:apply-templates select="bcl:text[1]"/>
            </p>
			      </xsl:when>
		       <xsl:otherwise>
			         <p class="amd para temp">
				           <a name="{@id}"/>
				           <xsl:apply-templates select="bcl:text[1]"/>
			         </p>
		       </xsl:otherwise>
		    </xsl:choose>
		    <xsl:apply-templates select="*[not(self::bcl:num) and not(self::bcl:text[not(preceding-sibling::bcl:text)])]"/>
	  </xsl:template>
	  <!-- bcl:paragraph/bcl:text -->
	<xsl:template match="amd:paragraph/bcl:text[not(position() = 1)]">
		    <p class="amd-para sandwich">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>
	  <!-- bcl:paragraph/bcl:num -->
	<xsl:template match="amd:paragraph/bcl:num">
		    <xsl:apply-templates/>
	  </xsl:template>
	  <xsl:template match="amd:paragraph/bcl:subsection">
		    <p class=" amd sub">
         <xsl:apply-templates/>
      </p>
	  </xsl:template>
	
	  <xsl:template match="amd:subparagraph">
		
			   <p class="amd-subpara">
				     <a name="{@id}"/>
				     <xsl:choose>
					       <xsl:when test="bcl:num">
						         <span class="amd-num">
                  <span class="amd-holder">
						               <xsl:apply-templates select="bcl:num"/>
                  </span>
               </span>
						         <xsl:text> </xsl:text>
						         <xsl:apply-templates select="bcl:text[1]"/>
					       </xsl:when>
					       <xsl:otherwise>
						         <xsl:apply-templates select="bcl:text[1]"/>
					       </xsl:otherwise>
				     </xsl:choose>
			   </p>
		    <div class="section-amd-subpara">
			      <p class="sub">
				        <a name="{bcl:subsection[1]/@id}"/>
				        <span class="num">
               <span class="holder">
                  <xsl:apply-templates select="bcl:subsection[1]/bcl:num"/>
               </span>
            </span>
				        <xsl:apply-templates select="bcl:subsection[1]/bcl:text"/>
			      </p>
			      <xsl:apply-templates select="*[not(self::bcl:num) and not(self::bcl:text[not(preceding-sibling::bcl:text)])]"/>
		    </div>
	  </xsl:template>
	  <xsl:template match="amd:subparagraph/bcl:text[not(position() = 1)]">
		    <p class="amd-subpara sandwich">
			      <xsl:apply-templates/>
		    </p>
	  </xsl:template>
	  <xsl:template match="byl:explannote">
		    <div>
			      <a href="link" onclick="showhide(this);return false;">
				        <img src="/civix/template/coa/assets/gov/images/explan-button.jpg"
                 class="button"
                 title="Explanatory Note"
                 width="112"
                 height="15"
                 border="0"/>
			      </a>
			      <div class="explannote bylaw" style="display: none;">
            <p>
               <xsl:apply-templates/>
            </p>
         </div>
		    </div>
	  </xsl:template>
	  <xsl:template match="amd:explannote">
		    <div>
			      <a href="link" onclick="showhide(this);return false;">
				        <img src="/civix/template/coa/assets/gov/images/explan-button.jpg"
                 class="button"
                 title="Explanatory Note"
                 width="112"
                 height="15"
                 border="0"/>
			      </a>
			      <div class="explannote" style="display: none;">
            <p>
               <xsl:apply-templates/>
            </p>
         </div>
		    </div>
	  </xsl:template>
	
	  <xsl:template match="amd:explannote/bcl:num">
		    <xsl:apply-templates/>
	  </xsl:template>
	
	  <xsl:template match="amd:explandescriptor">
      <strong>
         <em>
            <xsl:apply-templates/>
         </em>
      </strong>
   </xsl:template>
	
	  <xsl:template match="byl:approvals">
		    <span class="byl_aps">
			      <xsl:apply-templates/>
		    </span>
	  </xsl:template>
	  <xsl:template match="byl:approval">
		    <span class="byl_appr">
         <xsl:apply-templates/>
      </span>
	  </xsl:template>
	  <xsl:template match="byl:signatureblock">
		    <xsl:if test="not(@publish='false')">
			      <span class="byl_sigblock">
				        <xsl:apply-templates/>
			      </span>
		    </xsl:if>
	  </xsl:template>
	  <xsl:template match="byl:signature[1]">
		    <p class="byl_sig1">
         <span>
            <xsl:apply-templates/>
         </span>
      </p>
	  </xsl:template>
	  <xsl:template match="byl:signature[2]">
		    <p class="byl_sig2">
         <span>
            <xsl:apply-templates/>
         </span>
      </p>
	  </xsl:template>
	  <xsl:template match="byl:name">
		    <xsl:apply-templates/>,
	</xsl:template>
	
	  <xsl:template match="bcl:list">
		    <xsl:variable name="classname">
         <xsl:value-of select="concat(parent::node()/local-name(), '-list')"/>
      </xsl:variable>
		    <xsl:choose>
			      <xsl:when test="@type='bullet'">
				        <ul class="{$classname}" type="bullet">
					          <xsl:apply-templates/>
				        </ul>
			      </xsl:when>
			      <xsl:when test="@type='text'">
				        <ul class="{$classname}" type="text">
					          <xsl:apply-templates/>
				        </ul>
			      </xsl:when>
			      <xsl:otherwise>
				        <xsl:variable select="@type" name="type"/>
				        <xsl:if test="@type">
					          <ol class="{$classname}" type="{$type}">
						            <xsl:apply-templates/>
					          </ol>
				        </xsl:if>
			      </xsl:otherwise>
		    </xsl:choose>
	  </xsl:template>
	  <xsl:template match="bcl:item">
		    <li class="bullet-item">
			      <xsl:apply-templates/>
		    </li>
	  </xsl:template>
	  <xsl:template match="bcl:item">
		    <li class="text-item">
			      <xsl:apply-templates/>
		    </li>
	  </xsl:template>
	  <xsl:template match="bcl:num-item">
		    <li class="text-item">
			      <xsl:apply-templates/>
		    </li>
	  </xsl:template>
	
	  <!-- Oasis Table Title -->
	<!--moved this to bcleg xsl-->
	<!--<xsl:template match="oasis:tcaption">
		<caption>
			<xsl:for-each select="oasis:line">
				<p><xsl:apply-templates/></p>
			</xsl:for-each>
		</caption>
	</xsl:template>-->

	<xsl:template match="in:link">
		    <xsl:if test="descendant::hit">
			      <xsl:variable select="descendant::hit[1]" name="hit"/>
			      <a name="hit{$hit/@loc}{$hit/@num}"/>
		    </xsl:if>
		    <xsl:variable name="href">
			      <xsl:call-template name="replace-string">
				        <xsl:with-param name="text" select="@xlink:href"/>
				        <xsl:with-param name="replace" select="'/legislation/'"/>
				        <xsl:with-param name="with" select="'/civix/document/id/complete/statreg/'"/>
			      </xsl:call-template>
		    </xsl:variable>
		    <xsl:element name="a">
			      <xsl:attribute name="href">
				        <xsl:value-of select="replace(normalize-space(translate($href, ' ', '')), 'municipal.qp.gov.bc.ca', 'laws.abbotsford.ca')"/>
			      </xsl:attribute>
			      <xsl:if test="contains(@xlink:href,'https://municipal.qp.gov.bc.ca/') or contains(@xlink:href,'https://laws.abbotsford.ca/')">
				        <xsl:attribute name="class">
					          <xsl:value-of select="'cross-reference'"/>
				        </xsl:attribute>
			      </xsl:if>
			      <xsl:apply-templates/>
		    </xsl:element>
	  </xsl:template>
	  <xsl:template name="refs">
		    <xsl:param name="ref"/>
		    <xsl:for-each select="$ref/byl:ref">		
			      <xsl:if test="position()=1">
				        <xsl:value-of select="parent::node()/@prefix"/>
			      </xsl:if> <xsl:choose>
				        <xsl:when test="@provision = 'section'">
               <xsl:value-of select="@value"/>
            </xsl:when>
				        <xsl:otherwise>(<xsl:value-of select="@value"/>)</xsl:otherwise>
			      </xsl:choose>			
		    </xsl:for-each>
		
	  </xsl:template>

	  <xsl:template match="byl:crossref">
		    <xsl:apply-templates select="byl:rgroup"/>
	  </xsl:template>

	  <xsl:template match="byl:rgroup[(byl:ref[position()=last()]/@op = 'to')]">
		    <xsl:variable select="following-sibling::byl:rgroup[1]/byl:ref[position()=last()]/@xlink:href"
                    name="href2"/>
		    <a class="cross-reference"
         href="{byl:ref[position()=last()]/@xlink:href}"
         href2="{$href2}">	
			      <xsl:call-template name="refs">
				        <xsl:with-param name="ref" select="."/>
			      </xsl:call-template>
			
			      <xsl:value-of select="' to'"/>
			      <xsl:call-template name="refs">
				        <xsl:with-param name="ref" select="following-sibling::byl:rgroup[1]"/>
			      </xsl:call-template>
		    </a>
	  </xsl:template>
	
	  <xsl:template match="byl:rgroup[not(byl:ref[position()=last()]/@op = 'to')]">
		    <xsl:if test="not(preceding-sibling::byl:rgroup[1]/byl:ref[position() = last()]/@op = 'to')">
			      <a class="cross-reference" href="{byl:ref[position()=last()]/@xlink:href}">	
				        <xsl:for-each select="byl:ref">		
					          <xsl:if test="position()=1">
						            <xsl:value-of select="parent::node()/@prefix"/>
					          </xsl:if> <xsl:choose>
						            <xsl:when test="@provision = 'section'">
                     <xsl:value-of select="@value"/>
                  </xsl:when>
						            <xsl:otherwise>(<xsl:value-of select="@value"/>)</xsl:otherwise>
					          </xsl:choose>
					          <!-- if rgroup has an operator -->				
				</xsl:for-each>
			      </a>
			      <xsl:choose>
				        <xsl:when test="byl:ref[position()=last()]/@op">
					          <xsl:if test="not(byl:ref[position()=last()]/@op = ',')"> </xsl:if>
					          <xsl:value-of select="byl:ref[position()=last()]/@op"/>
				        </xsl:when>
			      </xsl:choose>
		    </xsl:if>
	  </xsl:template>
	
	  <xsl:template match="in:ref">
		    <a class="cross-reference" href="{@xlink:href}">	
			      <xsl:value-of select="text()"/>
		    </a>
	  </xsl:template>
	
	  <!-- oasis:table for bylaws  - Added table width, div wrapper with class name -->
	<xsl:template match="oasis:table" priority="10">
		    <xsl:variable name="classname">
         <xsl:value-of select="concat(parent::node()/local-name(), '-table')"/>
      </xsl:variable>
		    <div class="{$classname}">
		       <xsl:element name="table">
			         <xsl:choose>
				           <xsl:when test="@style='borderall-header'">
					             <xsl:attribute name="cellSpacing">0</xsl:attribute>
					             <xsl:attribute name="cellPadding">3</xsl:attribute>
					             <xsl:attribute name="class">borderall-header</xsl:attribute>
				           </xsl:when>
				           <xsl:when test="@style='borderall'">
					             <xsl:attribute name="cellSpacing">0</xsl:attribute>
					             <xsl:attribute name="cellPadding">3</xsl:attribute>
					             <xsl:attribute name="class">borderall</xsl:attribute>
				           </xsl:when>
				           <xsl:when test="@style='grid'">
					             <xsl:attribute name="cellSpacing">0</xsl:attribute>
					             <xsl:attribute name="cellPadding">3</xsl:attribute>
					             <xsl:attribute name="border">0</xsl:attribute>
					             <xsl:attribute name="class">grid</xsl:attribute>
				           </xsl:when>
				           <xsl:when test="@style='border-horizontal'">
					             <xsl:attribute name="cellSpacing">0</xsl:attribute>
					             <xsl:attribute name="cellPadding">3</xsl:attribute>
					             <xsl:attribute name="border">1</xsl:attribute>
					             <xsl:attribute name="class">border-horizontal</xsl:attribute>
				           </xsl:when>
			         </xsl:choose>
			         <xsl:if test="@width and not(@fixedwidth='false')">
					          <xsl:attribute name="width">
						            <xsl:value-of select="@width"/>
					          </xsl:attribute>
			         </xsl:if>
			         <xsl:if test="./@align">
				           <xsl:attribute name="align">
					             <xsl:value-of select="./@align"/>
				           </xsl:attribute>
			         </xsl:if>
			         <xsl:apply-templates/>
		       </xsl:element>
      </div>
	  </xsl:template>
	
	  <!-- oasis:tgroup for bylaws - Add colgroup with column widths -->
	<xsl:template match="oasis:tgroup" priority="10">
		    <xsl:variable name="totalColWidth">
         <xsl:value-of select="sum(./oasis:colspec/number(substring(@colwidth, 1, string-length(@colwidth) - 1)))"/>
      </xsl:variable>
		    <colgroup>
			      <xsl:for-each select="oasis:colspec">
				<!-- Convert Relative Column Width to Percentage Width -->
				<xsl:variable name="colWidthNum">
               <xsl:value-of select="number(substring(@colwidth, 1, string-length(@colwidth) - 1))"/>
            </xsl:variable>
				        <xsl:variable name="percentageWidth">
               <xsl:value-of select="($colWidthNum div $totalColWidth)*100"/>
            </xsl:variable>
				        <col style="width:{$percentageWidth}%"/>
			      </xsl:for-each>
		    </colgroup>
		    <xsl:apply-templates/>
	  </xsl:template>
	
	  <xsl:template match="oasis:thead" priority="10">
		    <thead>
			      <xsl:apply-templates/>
		    </thead>
	  </xsl:template>
	
	  <xsl:template match="oasis:tbody" priority="10">
		    <tbody>
			      <xsl:apply-templates/>
		    </tbody>
	  </xsl:template>
	
	  <!-- oasis:entry for bylaws - Added column width -->
	<xsl:template match="oasis:entry" priority="10">
		    <td>
			      <xsl:for-each select="@*">
				        <xsl:choose>
					          <xsl:when test="name() = 'morerows'">
						            <xsl:attribute name="rowspan">
							              <xsl:value-of select="number(.) + 1"/>
						            </xsl:attribute>
					          </xsl:when>
					          <xsl:otherwise>
						            <xsl:attribute name="{name()}">
							              <xsl:value-of select="."/>
						            </xsl:attribute>
					          </xsl:otherwise>
				        </xsl:choose>
				
			      </xsl:for-each>
			      <!-- <xsl:variable name="col_name"><xsl:value-of select="./@colname"/></xsl:variable>
				<xsl:attribute name="width">
				<xsl:value-of select="ancestor::oasis:tgroup/oasis:colspec[@colname = $col_name]/@colwidth"/>
			</xsl:attribute>-->
			<xsl:apply-templates/>
		    </td>
	  </xsl:template>
	
	  <!-- oasis:line for bylaws -->
	<xsl:template match="oasis:line[parent::oasis:entry]" priority="10">
		    <xsl:choose>
			      <xsl:when test=". != ''">
				        <p>
               <xsl:apply-templates/>
            </p>
			      </xsl:when>
			      <xsl:otherwise> </xsl:otherwise>
		    </xsl:choose>
	  </xsl:template>
	
	  <!-- in:tl Text List for bylaws
	 When a text list appears in bcl:text, grab the name of the list's grandparent-->
	<xsl:template match="in:tl" priority="10">
		    <xsl:choose>
			      <xsl:when test="name(parent::node())='bcl:text'">
				        <xsl:variable name="classname">
               <xsl:value-of select="concat(parent::node()/parent::node()/local-name(), '-list')"/>
            </xsl:variable>
				        <ul class="{$classname}" type="text">
					          <xsl:apply-templates/>
				        </ul>
			      </xsl:when>
			      <xsl:otherwise>
				        <xsl:variable name="classname">
               <xsl:value-of select="concat(parent::node()/local-name(), '-list')"/>
            </xsl:variable>
				        <ul class="{$classname}" type="text">
					          <xsl:apply-templates/>
				        </ul>
			      </xsl:otherwise>
		    </xsl:choose>
	  </xsl:template>
	
	  <!-- inline decriptor -->
	<xsl:template match="in:desc">
		    <span class="inline-descriptor">
         <xsl:apply-templates/>
      </span>
	  </xsl:template>
	
	  <xsl:template name="notesSummary">
		    <xsl:variable name="numOfNotes">
			      <xsl:choose>
				        <xsl:when test="count(//*:explannote) &gt; 1">
					          <xsl:text>Explanatory Notes</xsl:text>
				        </xsl:when>
				        <xsl:when test="count(//*:explannote) = 1 ">
					          <xsl:text>Explanatory Note</xsl:text>
				        </xsl:when>
			      </xsl:choose>
		    </xsl:variable>
		    <h3 align="center">
         <br/>
         <xsl:value-of select="$numOfNotes"/>
      </h3>
		    <xsl:apply-templates select="//amd:explannote | //byl:explannote" mode="sum"/>
	  </xsl:template>
	
	  <xsl:template match="amd:explannote | byl:explannote" mode="sum">
		    <div class="explannoteSummary">
         <p>
            <xsl:apply-templates/>
         </p>
      </div>
	  </xsl:template>
	
	  <!-- images -->
	<xsl:template match="in:graphic">			
		    <xsl:choose>
			      <xsl:when test="@align != ''">
				        <xsl:element name="p">
					          <xsl:attribute name="align">
						            <xsl:value-of select="@align"/>
					          </xsl:attribute>
					          <xsl:element name="img">
						            <xsl:attribute name="src">
							              <xsl:value-of select="@href"/>
						            </xsl:attribute>
						            <xsl:attribute name="height">
							              <xsl:value-of select="@height"/>
						            </xsl:attribute>
						            <xsl:attribute name="width">
							              <xsl:value-of select="@width"/>
						            </xsl:attribute>
					          </xsl:element>
				        </xsl:element>
			      </xsl:when>
			      <xsl:when test="parent::bcl:lefttext | parent::bcl:centertext | parent::bcl:righttext">
				        <xsl:element name="img">
					          <xsl:attribute name="src">
						            <xsl:value-of select="@href"/>
					          </xsl:attribute>
					          <xsl:attribute name="height">
						            <xsl:value-of select="@height"/>
					          </xsl:attribute>
					          <xsl:attribute name="width">
						            <xsl:value-of select="@width"/>
					          </xsl:attribute>
				        </xsl:element>
			      </xsl:when>
			      <xsl:otherwise>
				        <xsl:element name="p">
					          <xsl:attribute name="class">
						            <xsl:value-of select="concat(parent::node()/parent::node()/local-name(), '-image')"/>
					          </xsl:attribute>
					          <xsl:element name="img">
						            <xsl:attribute name="src">
							              <xsl:value-of select="@href"/>
						            </xsl:attribute>
						            <xsl:attribute name="height">
							              <xsl:value-of select="@height"/>
						            </xsl:attribute>
						            <xsl:attribute name="width">
							              <xsl:value-of select="@width"/>
						            </xsl:attribute>
					          </xsl:element>
				        </xsl:element>
			      </xsl:otherwise>
		    </xsl:choose>	
	  </xsl:template>
	
	  <xsl:template match="in:graphic[child::in:caption]">
		    <xsl:variable name="cap-pos">
         <xsl:value-of select="./in:caption/@position"/>
      </xsl:variable>
		    <xsl:variable name="cap-align">
         <xsl:value-of select="./in:caption/@align"/>
      </xsl:variable>
		    <xsl:choose>
			      <xsl:when test="@align != ''">
				        <div>
					          <xsl:attribute name="class">
						            <xsl:value-of select="'img-with-caption '"/>
						            <xsl:value-of select="@align"/>
					          </xsl:attribute>
					          <xsl:if test="$cap-pos = 'top'">
						            <xsl:call-template name="im-caption">
							              <xsl:with-param name="direction" select="$cap-align"/>
						            </xsl:call-template>
					          </xsl:if>
					          <xsl:element name="img">
						            <xsl:attribute name="src">
							              <xsl:value-of select="@href"/>
						            </xsl:attribute>
						            <xsl:attribute name="height">
							              <xsl:value-of select="@height"/>
						            </xsl:attribute>
						            <xsl:attribute name="width">
							              <xsl:value-of select="@width"/>
						            </xsl:attribute>
					          </xsl:element>
					          <xsl:if test="$cap-pos = 'bottom'">
						            <xsl:call-template name="im-caption">
							              <xsl:with-param name="direction" select="$cap-align"/>
						            </xsl:call-template>
					          </xsl:if>
				        </div>
			      </xsl:when>
			      <xsl:when test="parent::bcl:lefttext | parent::bcl:centertext | parent::bcl:righttext">
				        <div>
					          <xsl:attribute name="class">
						            <xsl:value-of select="'img-with-caption '"/>
						            <xsl:value-of select="replace(parent::node()/local-name(), 'text', '')"/>
					          </xsl:attribute>
					          <xsl:if test="$cap-pos = 'top'">
						            <xsl:call-template name="im-caption">
							              <xsl:with-param name="direction" select="$cap-align"/>
						            </xsl:call-template>
					          </xsl:if>
					          <xsl:element name="img">
						            <xsl:attribute name="src">
							              <xsl:value-of select="@href"/>
						            </xsl:attribute>
						            <xsl:attribute name="height">
							              <xsl:value-of select="@height"/>
						            </xsl:attribute>
						            <xsl:attribute name="width">
							              <xsl:value-of select="@width"/>
						            </xsl:attribute>
					          </xsl:element>
					          <xsl:if test="$cap-pos = 'bottom'">
						            <xsl:call-template name="im-caption">
							              <xsl:with-param name="direction" select="$cap-align"/>
						            </xsl:call-template>
					          </xsl:if>
				        </div>
			      </xsl:when>
			      <xsl:otherwise>
				        <div>			
					          <xsl:attribute name="class">
						            <xsl:value-of select="'img-with-caption '"/>
						            <xsl:value-of select="concat(parent::node()/parent::node()/local-name(), '-image')"/>
					          </xsl:attribute>
					          <xsl:if test="$cap-pos = 'top'">
						            <xsl:call-template name="im-caption">
							              <xsl:with-param name="direction" select="$cap-align"/>
						            </xsl:call-template>
					          </xsl:if>
					          <xsl:element name="img">
						            <xsl:attribute name="src">
							              <xsl:value-of select="@href"/>
						            </xsl:attribute>
						            <xsl:attribute name="height">
							              <xsl:value-of select="@height"/>
						            </xsl:attribute>
						            <xsl:attribute name="width">
							              <xsl:value-of select="@width"/>
						            </xsl:attribute>
					          </xsl:element>
					          <xsl:if test="$cap-pos = 'bottom'">
						            <xsl:call-template name="im-caption">
							              <xsl:with-param name="direction" select="$cap-align"/>
						            </xsl:call-template>
					          </xsl:if>
				        </div>
			      </xsl:otherwise>
		    </xsl:choose>		
	  </xsl:template>
	
	  <xsl:template name="im-caption">
		    <xsl:param name="direction" required="yes" as="item()"/>
		    <xsl:element name="p">
			      <xsl:attribute name="align">
            <xsl:value-of select="$direction"/>
         </xsl:attribute>
			      <!--<xsl:attribute name="position"></xsl:attribute>-->
			<xsl:apply-templates/>
		    </xsl:element>
	  </xsl:template>
		
</xsl:stylesheet>
