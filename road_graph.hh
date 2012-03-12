// Tempus core data structures
// (c) 2012 Oslandia
// MIT License
/**
   This file contains declarations of classes used to model road graphs

   It generally maps to the database's schema: one class exists for each table.
   Tables with 1<->N arity are represented by STL containers (vectors or lists)
   External keys are represented by pointers to other classes.
   
   Road::Node and Road::Section classes are used to build a BGL road graph as "bundled" edge and vertex properties
 */

#ifndef TEMPUS_ROAD_GRAPH_HH
#define TEMPUS_ROAD_GRAPH_HH

#include "common.hh"
#include <boost/graph/adjacency_list.hpp>

namespace Tempus
{
    namespace Road
    {
	///
	/// Storage types used to make a road graph
	typedef boost::vecS VertexListType;
	typedef boost::vecS EdgeListType;

	///
	/// To make a long line short: VertexDescriptor is either typedef'd to size_t or to a pointer,
	/// depending on VertexListType and EdgeListType used to represent lists of vertices (vecS, listS, etc.)
	typedef typename boost::mpl::if_<typename boost::detail::is_random_access<VertexListType>::type, size_t, void*>::type Vertex;
	/// see adjacency_list.hpp
	typedef typename boost::detail::edge_desc_impl<boost::directed_tag, Vertex> Edge;

	class Node;
	class Section;
	///
	/// The final road graph type
	typedef boost::adjacency_list<VertexListType, EdgeListType, boost::directedS, Node, Section > Graph;

	///
	/// Used as Vertex.
	/// Refers to the 'road_node' DB's table
	struct Node : public Base
	{
	    /// This is a shortcut to the vertex index in the corresponding graph, if any.
	    /// Needed to speedup access to a graph's vertex from a Node.
	    /// Can be null
	    Graph* graph;
	    Vertex vertex;

	    bool is_junction;
	    bool is_bifurcation;
	};
	
	///
	/// Used as Directed Edge.
	/// Refers to the 'road_section' DB's table
	struct Section : public Base
	{
	    /// This is a shortcut to the edge index in the corresponding graph, if any.
	    /// Needed to speedup access to a graph's edge from a Section.
	    /// Can be null
	    Graph* graph;
	    Edge edge;

	    RoadType      road_type;
	    int           transport_type_ft; ///< bitfield of TransportTypeId
	    int           transport_type_tf; ///< bitfield of TransportTypeId
	    double        length;
	    double        car_speed_limit;
	    double        car_average_speed;
	    double        bus_average_speed;
	    std::string   road_name;
	    std::string   address_left_side;
	    std::string   address_right_side;
	    int           lane;
	    bool          is_roundabout;
	    bool          is_bridge;
	    bool          is_tunnel;
	    bool          is_ramp;
	    bool          is_tollway;
	};
    };

    ///
    /// refers to the 'poi' DB's table
    struct POI : public Base
    {
	enum PoiType
	{
	    TypeCarPark = 1,
	    TypeSharedCarPoint,
	    TypeCyclePark,
	    TypeSharedCyclePoint,
	    TypeUserPOI
	};
	int poi_type;

	std::string name;
	int parking_transport_type; ///< bitfield of TransportTypeId

	///
	/// Link to a road section.
	/// Must not be null.
	Road::Section* road_section;
	double abscissa_road_section;

	bool check_consistency()
	{
	    EXPECT( road_section != 0 );
	    return true;
	}
    }; // Road namespace
}; // Tempus namespace

#endif
