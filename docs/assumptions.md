# Assumptions
- Score = 0.25 temperature + 0.20 solar + 0.15 surface + 0.20 duration + 0.10 (100-shade) + 0.05 (100-greenery) + 0.05 (100-breeze), clamped 0-100, then multiplied by a profile factor (pedestrian 1.00, cyclist 1.05, outdoor worker 1.10). The profile factors are assumptions, not research results.
- Time buckets: before 11:00 = morning, 11:00-14:59 = midday, 15:00 onward = evening. Low evening sun lets building shadows add shade (`canyon` x 60 points).
- Duration index = minutes / 30 x 100, capped at 100. Duration values are demo values; a 15-20 minute trip suits a short campus-scale walk or ride better than the full corridor.
- Recommendation rule: pick the cooler route only if it saves at least 15 points for at most 10 extra minutes; otherwise recommend the fastest.
- Scoring runs on pre-defined candidate routes. Live routing (e.g. Amazon Location Service) is future work.
