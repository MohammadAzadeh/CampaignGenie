from pages.agents import FirstAgent

# This playground is meant to be used in Agent-UI,
# Also, Available on localhost:7777
playground_app = Playground(agents=[FirstAgent().agent])
app = playground_app.get_app()

if __name__ == "__main__":
    playground_app.serve("main:app", reload=True)
