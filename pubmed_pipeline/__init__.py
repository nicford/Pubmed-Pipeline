from .pubmedPipeline import PubmedPipelineSetup, PubmedPipelineUpdate
import pip, glob

__all__ = ['PubmedPipelineSetup', 'PubmedPipelineUpdate']

# for path in glob.glob("./*.whl")
# pip.main(["install", path])