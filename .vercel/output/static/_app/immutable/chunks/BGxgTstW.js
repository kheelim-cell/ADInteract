import{q as i}from"./C05Uplpq.js";function p(t){return t.replace(/'/g,"''")}function N(t){const r=[];return t?.district&&r.push(`district = '${p(t.district)}'`),t?.propertyType&&r.push(`property_type = '${p(t.propertyType)}'`),t?.layout&&r.push(`layout = '${p(t.layout)}'`),r.length?" AND "+r.join(" AND "):""}function y(t){return t?.layout?`layout = '${p(t.layout)}'`:"layout = 'all beds'"}async function m(t,r,c=5,a){const n=N({...a,district:null});return(await i(`
		WITH cur AS (
			SELECT district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS current_rate,
			       COUNT(*) AS tx_count
			FROM transactions
			WHERE YEAR(sale_date) = ${t}
			  AND rate_per_sqft IS NOT NULL AND rate_per_sqft > 0
			  ${n}
			GROUP BY district
			HAVING COUNT(*) >= 10
		),
		prv AS (
			SELECT district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS prev_rate
			FROM transactions
			WHERE YEAR(sale_date) = ${r}
			  AND rate_per_sqft IS NOT NULL AND rate_per_sqft > 0
			  ${n}
			GROUP BY district
			HAVING COUNT(*) >= 10
		)
		SELECT c.district,
		       c.current_rate,
		       p.prev_rate,
		       ROUND(((c.current_rate - p.prev_rate) / p.prev_rate) * 100, 1) AS yoy_pct,
		       c.tx_count
		FROM cur c
		JOIN prv p ON c.district = p.district
		WHERE p.prev_rate > 0
		ORDER BY yoy_pct DESC
		LIMIT ${c}
	`)).map(e=>({name:e.district,currentValue:e.current_rate,prevValue:e.prev_rate,yoyPct:e.yoy_pct,txCount:e.tx_count}))}async function R(t,r,c=5,a){const n=N(a);return(await i(`
		WITH cur AS (
			SELECT project_name, district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS current_rate,
			       COUNT(*) AS tx_count
			FROM transactions
			WHERE YEAR(sale_date) = ${t}
			  AND rate_per_sqft IS NOT NULL AND rate_per_sqft > 0
			  AND project_name IS NOT NULL AND project_name != ''
			  AND LOWER(project_name) != 'private'
			  ${n}
			GROUP BY project_name, district
			HAVING COUNT(*) >= 5
		),
		prv AS (
			SELECT project_name,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS prev_rate
			FROM transactions
			WHERE YEAR(sale_date) = ${r}
			  AND rate_per_sqft IS NOT NULL AND rate_per_sqft > 0
			  AND project_name IS NOT NULL AND project_name != ''
			  AND LOWER(project_name) != 'private'
			  ${n}
			GROUP BY project_name
			HAVING COUNT(*) >= 5
		)
		SELECT c.project_name,
		       c.district,
		       c.current_rate,
		       p.prev_rate,
		       ROUND(((c.current_rate - p.prev_rate) / p.prev_rate) * 100, 1) AS yoy_pct,
		       c.tx_count
		FROM cur c
		JOIN prv p ON c.project_name = p.project_name
		WHERE p.prev_rate > 0
		ORDER BY yoy_pct DESC
		LIMIT ${c}
	`)).map(e=>({name:e.project_name,district:e.district,currentValue:e.current_rate,prevValue:e.prev_rate,yoyPct:e.yoy_pct,txCount:e.tx_count}))}async function A(t,r=5,c){const a=t-1,n=c?.district?` AND district = '${p(c.district)}'`:"",s=y(c);return(await i(`
		WITH cur AS (
			-- Use real per-typology rows (not the aggregate sentinel) for accuracy.
			-- Median of medians across typologies gives a figure consistent with
			-- what users see in the Rental tab.
			SELECT project_name,
			       ANY_VALUE(district) AS district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS current_rent
			FROM rental
			WHERE year = ${t}
			  AND typology != 'All property types'
			  AND ${s}
			  AND rent_type = 'All types'
			  AND median_rent > 0
			  AND project_name IS NOT NULL AND project_name != ''
			  AND LOWER(project_name) != 'private'
			  ${n}
			GROUP BY project_name
		),
		prv AS (
			SELECT project_name,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS prev_rent
			FROM rental
			WHERE year = ${a}
			  AND typology != 'All property types'
			  AND ${s}
			  AND rent_type = 'All types'
			  AND median_rent > 0
			  AND project_name IS NOT NULL AND project_name != ''
			  AND LOWER(project_name) != 'private'
			  ${n}
			GROUP BY project_name
		)
		SELECT c.project_name,
		       c.district,
		       c.current_rent,
		       p.prev_rent,
		       ROUND(((c.current_rent - p.prev_rent) / p.prev_rent) * 100, 1) AS yoy_pct
		FROM cur c
		JOIN prv p ON c.project_name = p.project_name
		WHERE p.prev_rent > 0
		ORDER BY yoy_pct DESC
		LIMIT ${r}
	`)).map(o=>({name:o.project_name,district:o.district,currentValue:o.current_rent,prevValue:o.prev_rent,yoyPct:o.yoy_pct}))}async function O(t,r,c=5,a){const n=a?.district?`AND district      = '${p(a.district)}'`:"",s=a?.layout?`AND layout        = '${p(a.layout)}'`:"",e=a?.propertyType?`AND property_type = '${p(a.propertyType)}'`:"",o=y(a);return(await i(`
		WITH sales AS (
			SELECT community, district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_aed) AS median_sale_price,
			       COUNT(*) AS sale_count
			FROM transactions
			WHERE YEAR(sale_date) = ${t}
			  AND price_aed IS NOT NULL AND price_aed > 0
			  AND community IS NOT NULL AND community != ''
			  ${n}
			  ${s}
			  ${e}
			GROUP BY community, district
			HAVING COUNT(*) >= ${c}
		),
		proj_map AS (
			SELECT DISTINCT LOWER(TRIM(project_name)) AS proj_key, community
			FROM transactions
			WHERE YEAR(sale_date) = ${t}
			  AND community IS NOT NULL AND community != ''
			  AND project_name IS NOT NULL AND project_name != ''
		),
		rents AS (
			SELECT pm.community,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY r.median_rent) AS median_annual_rent,
			       COUNT(DISTINCT r.project_name) AS project_count
			FROM rental r
			JOIN proj_map pm ON LOWER(TRIM(r.project_name)) = pm.proj_key
			WHERE r.year = ${r}
			  AND r.typology = 'All property types'
			  AND r.${o}
			  AND r.rent_type = 'All types'
			  AND r.median_rent > 0
			GROUP BY pm.community
		)
		SELECT s.community,
		       s.district,
		       s.median_sale_price,
		       r.median_annual_rent,
		       ROUND((r.median_annual_rent / s.median_sale_price) * 100, 2) AS gross_yield_pct,
		       s.sale_count,
		       r.project_count
		FROM sales s
		JOIN rents r ON s.community = r.community
		WHERE s.median_sale_price > 0
		ORDER BY gross_yield_pct DESC
	`)).map(_=>({community:_.community,district:_.district,medianSalePrice:_.median_sale_price,medianAnnualRent:_.median_annual_rent,grossYieldPct:_.gross_yield_pct,saleCount:_.sale_count,projectCount:_.project_count}))}export{m as a,R as b,A as c,O as q};
