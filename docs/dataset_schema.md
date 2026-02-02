# Dataset Schema (Flexible Loader)

Training CSV is expected in `data/raw/`.

## Accepted text columns (priority order)
1. `text`
2. `clause`
3. `sentence`
4. `content`

## Accepted label columns (priority order)
1. `label`
2. `category`
3. `clause_type`
4. `type`

The loader should pick the first existing column in each list.

## Minimum requirements
- At least one accepted text column
- At least one accepted label column
- UTF-8 encoded CSV recommended
