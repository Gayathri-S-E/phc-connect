import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://neondb_owner:npg_Zdm2oDx0eEIf@ep-damp-surf-b361xw4r-pooler.c-4.ap-southeast-1.aws.neon.tech/neondb?ssl=require')
    
    print("Dropping schema public...")
    await conn.execute('DROP SCHEMA public CASCADE;')
    print("Creating schema public...")
    await conn.execute('CREATE SCHEMA public;')
    await conn.execute('GRANT ALL ON SCHEMA public TO public;')
    
    print("Dropping stray enum types...")
    types = await conn.fetch("SELECT typname FROM pg_type WHERE typtype = 'e';")
    for t in types:
        await conn.execute(f"DROP TYPE IF EXISTS {t['typname']} CASCADE;")
        
    print("Done resetting database!")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
