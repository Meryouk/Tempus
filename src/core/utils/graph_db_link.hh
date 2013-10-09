// (c) 2013 Oslandia
// MIT License
// Utility functions that make a link between graph indexes and DB ids

#include <boost/graph/graph_traits.hpp>

#include "../common.hh"
#include "../road_graph.hh"
#include "../public_transport_graph.hh"
#include "../multimodal_graph.hh"
#include "../db.hh"

namespace Tempus
{
    ///
    /// Get a vertex descriptor from its database's id.
    /// This is templated in a way that it is compliant with Road::Vertex, PublicTransport::Vertex
    template <class G>
    typename boost::graph_traits<G>::vertex_descriptor vertex_from_id( Tempus::db_id_t db_id, G& graph)
    {
    	typename boost::graph_traits<G>::vertex_iterator vi, vi_end;
    	for ( boost::tie( vi, vi_end ) = vertices( graph ); vi != vi_end; vi++ )
    	{
    	    if ( graph[*vi].db_id == db_id )
    		return *vi;
    	}
    	// null element
    	return typename boost::graph_traits<G>::vertex_descriptor();
    }

    ///
    /// Get an edge descriptor from its database's id.
    /// This is templated in a way that it is compliant with Road::Edge
    /// A PublicTransport::Edge has no unique id associated.
    template <class G>
    typename boost::graph_traits<G>::edge_descriptor edge_from_id( Tempus::db_id_t db_id, G& graph)
    {
    	typename boost::graph_traits<G>::edge_iterator vi, vi_end;
    	for ( boost::tie( vi, vi_end ) = edges( graph ); vi != vi_end; vi++ )
    	{
    	    if ( graph[*vi].db_id == db_id )
    		return *vi;
    	}
    	// null element
    	return typename boost::graph_traits<G>::edge_descriptor();
    }

    ///
    /// Get 2D coordinates of a road vertex, from the database
    Point2D coordinates( const Road::Vertex& v, Db::Connection& db, const Road::Graph& graph );
    ///
    /// Get 2D coordinates of a public transport vertex, from the database
    Point2D coordinates( const PublicTransport::Vertex& v, Db::Connection& db, const PublicTransport::Graph& graph );
    ///
    /// Get 2D coordinates of a POI, from the database
    Point2D coordinates( const POI* poi, Db::Connection& db );
    ///
    /// Get 2D coordinates of a multimodal vertex, from the database
    Point2D coordinates( const Multimodal::Vertex& v, Db::Connection& db, const Multimodal::Graph& graph );
}
