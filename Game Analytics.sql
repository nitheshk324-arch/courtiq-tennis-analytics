#List all competitions along with their category name
SELECT
    c.competition_id,
    c.competition_name,
    cat.category_name
FROM competitions AS c
JOIN categories AS cat
    ON c.category_id = cat.category_id;
    
 #Count the number of competitions in each category
 SELECT 
    cat.category_name, 
    COUNT(c.competition_id) AS competition_count 
FROM 
    competitions c
JOIN 
    categories cat 
ON 
    c.category_id = cat.category_id
GROUP BY 
    cat.category_name
ORDER BY 
    competition_count DESC;

#Find all competitions of type 'doubles'
SELECT 
    c.competition_id, 
    c.competition_name, 
    cat.category_name 
FROM 
    competitions c
JOIN 
    categories cat 
ON 
    c.category_id = cat.category_id
WHERE 
    c.type = 'doubles';

#Get competitions that belong to a specific category (e.g., ITF Men)
SELECT 
    c.competition_id, 
    c.competition_name 
FROM 
    competitions c
JOIN 
    categories cat 
ON 
    c.category_id = cat.category_id
WHERE 
    cat.category_name = 'ITF Men';

#Identify parent competitions and their sub-competitions
SELECT 
    parent.competition_id AS parent_competition, 
    child.competition_name AS sub_competition 
FROM 
    competitions child
LEFT JOIN 
    competitions parent 
ON 
    child.parent_id = parent.competition_id
WHERE 
    child.parent_id IS NOT NULL;

#Analyze the distribution of competition types by category
SELECT 
    cat.category_name, 
    c.type, 
    COUNT(c.competition_id) AS type_count 
FROM 
    competitions c
JOIN 
    categories cat 
ON 
    c.category_id = cat.category_id
GROUP BY 
    cat.category_name, 
    c.type
ORDER BY 
    cat.category_name, 
    type_count DESC;
    
#List all competitions with no parent (top-level competitions)
SELECT 
    c.competition_id, 
    c.competition_name, 
    cat.category_name 
FROM 
    competitions c
JOIN 
    categories cat 
ON 
    c.category_id = cat.category_id
WHERE 
    c.parent_id IS NULL;

#List all venues along with their associated complex name
SELECT v.venue_id, v.venue_name, c.complex_name
FROM Venues v
JOIN Complexes c ON v.complex_id = c.complex_id;

#Count the number of venues in each complex
SELECT c.complex_name, COUNT(v.venue_id) AS venue_count
FROM Complexes c
LEFT JOIN Venues v ON c.complex_id = v.complex_id
GROUP BY c.complex_name;

#Get details of venues in a specific country (e.g., Chile)
SELECT venue_id, venue_name, city_name, country_name, timezone
FROM Venues
WHERE country_name = 'Chile';

#Identify all venues and their timezones
SELECT venue_id, venue_name, timezone
FROM Venues;

#Find complexes that have more than one venue
SELECT c.complex_name, COUNT(v.venue_id) AS venue_count
FROM Complexes c
JOIN Venues v ON c.complex_id = v.complex_id
GROUP BY c.complex_name
HAVING COUNT(v.venue_id) > 1;

#List venues grouped by country
SELECT country_name, STRING_AGG(venue_name, ', ') AS venues
FROM Venues
GROUP BY country_name;

#Find all venues for a specific complex (e.g., Nacional)
SELECT v.venue_id, v.venue_name, c.complex_name
FROM Venues v
JOIN Complexes c ON v.complex_id = c.complex_id
WHERE c.complex_name = 'Nacional';

#Get all competitors with their rank and points
SELECT c.name AS competitor_name, c.country, cr.rank, cr.points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id;

#Find competitors ranked in the top 5
SELECT c.name AS competitor_name, c.country, cr.rank, cr.points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
WHERE cr.rank <= 5
ORDER BY cr.rank ASC;

#List competitors with no rank movement (stable rank)
SELECT c.name AS competitor_name, c.country, cr.rank, cr.points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
WHERE cr.movement = 0;

#Get the total points of competitors from a specific country (e.g., Croatia)
SELECT c.country, SUM(cr.points) AS total_points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
WHERE c.country = 'Croatia'
GROUP BY c.country;

#Count the number of competitors per country
SELECT c.country, COUNT(c.competitor_id) AS competitor_count
FROM Competitors c
GROUP BY c.country;

#Find competitors with the highest points in the current week
SELECT c.name AS competitor_name, c.country, cr.rank, cr.points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
WHERE cr.points = (
    SELECT MAX(points)
    FROM Competitor_Rankings
);