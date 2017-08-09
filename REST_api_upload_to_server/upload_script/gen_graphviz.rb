require 'twb'

# puts   "┌ Documenting Workbooks with Tableau Tools"
# puts   "├ Adding Dashboard -> Worksheet -> Data Source graphs"

path = if ARGV.empty? then '*.twb' else ARGV[0] end
# puts   "├ Files matching: '#{path}'"
Dir.glob(path) do |twb|
  # puts "├ #{twb}"
  twb        = Twb::Workbook.new(twb)
  dotBuilder = Twb::Util::TwbDashSheetDataDotBuilder.new(twb)
  dotFile    = dotBuilder.dotFileName
  renderer   = Twb::Util::DotFileRenderer.new
  imageFile  = renderer.render(dotFile,'png')
  dash       = Twb::DocDashboardImageVert.new
  # only include if you want an additional twb constructed (WIP)
  # dash.image=(imageFile)
  # dash.title=('Dashboards, Worksheets, and Data Sources')
  # twb.addDocDashboard(dash)
  # twb.writeAppend('dot')
end
# puts   "└ Graphviz files generated"
