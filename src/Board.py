import pickle
from time import time
import cv2
import numpy as np
import CVAnalysis
from Square import Square
from util import iter_algebraic_notations

class Board:
	"""
		Class: Board
		------------
		class for representing everything about the board

		Member Variables:
			- image: numpy ndarray representing the image 
			- corners: list of point correspondances between board coordinates
						and image coordinates. (board_coords, image_coords, descriptor)
			- squares: list of SquareImage 

	"""

	def __init__ (self, name=None, image=None, BIH=None, board_points=None, image_points=None, sift_desc=None, filename=None):
		"""
			PRIVATE: Constructor
			--------------------
			constructs a BoardImage from it's constituent data
			or the filename of a saved one
		"""
		#=====[ CASE: from file ]=====
		if filename:
			self.construct_from_file (filename)
	
		#=====[ CASE: from BIH	]=====
		elif not None in [image, BIH]:
			self.construct_from_BIH (name, image, BIH)


		#=====[ CASE: from points	]=====
		else:
			if None in [name, image, board_points, image_points]:
				raise StandardError ("Must enter all data arguments or a filename")
			else:
				self.construct_from_points (name, image, board_points, image_points, sift_desc)


	def construct_from_file (self, filename):
		"""
			PRIVATE: construct_from_file
			----------------------------
			loads a previously-saved BoardImage
		"""
		self.load (filename)


	def construct_from_points (self, name, image, board_points, image_points, sift_desc):
		"""
			PRIVATE: construct_from_points
			------------------------------
			fills out this BoardImage based on passed in fields 
		"""
		#=====[ Step 1: set name	]=====
		if not name:
			self.name = str(time ())
		else:
			self.name = name

		#=====[ Step 2: set image	]=====
		self.image = image

		#=====[ Step 3: set corners	]=====
		assert len(board_points) == len(image_points)
		assert len(board_points) == len(sift_desc)
		self.board_points = board_points
		self.image_points = image_points
		self.sift_desc = sift_desc

		#=====[ Step 4: get BIH, squares ]=====
		self.get_BIH ()
		self.construct_squares ()


	def construct_from_BIH (self, name, image, BIH):
		"""
			PRIVATE: construct_from_BIH
			---------------------------
			fills out this BoardImage based on a BIH, assuming the image 
			that you computed it from came from the same chessboard, same 
			pose 
		"""
		#=====[ Step 1: set name	]=====
		if not name:
			self.name = str(time ())
		else:
			self.name = name

		#=====[ Step 1: set BIH/image	]=====
		self.BIH = BIH
		self.image = image

		#=====[ Step 2: set squares	]=====
		self.construct_squares ()

		#=====[ Step 3: set everything else	]=====
		self.board_points = None
		self.image_points = None 
		self.sift_desc = None





	####################################################################################################
	##############################[ --- DATA MANAGEMENT --- ]###########################################
	####################################################################################################	

	def parse_occlusions (self, filename):
		"""
			PRIVATE: parse_occlusions
			-------------------------
			given a filename containing occlusions, returns it in 
			list format 
		"""
		return [line.strip().split(' ') for line in open(filename, 'r').readlines ()]


	def add_occlusions (self, filename):
		"""
			PUBLIC: add_occlusions
			----------------------
			given the name of a file containing occlusions, this will 
			add them to each of the squares 
		"""
		#=====[ Step 1: parse occlusions	]=====
		occlusions = self.parse_occlusions (filename)

		#=====[ Step 2: add them one-by-one	]=====
		for i in range(8):
			for j in range(8):
				self.squares [i][j].add_occlusion (occlusions[i][j])


	def get_occlusion_features (self):
		"""
			PUBLIC: get_occlusions
			----------------------
			returns X, y
			X: np.mat where each row is a feature vector representing a square
			y: list of labels for X
		"""
		X = [s.get_occlusion_features () for s in self.iter_squares ()]
		y = [s.occlusion for s in self.iter_squares ()]
		return np.array (X), np.array(y)





	####################################################################################################
	##############################[ --- LOADING/SAVING --- ]############################################
	####################################################################################################	

	def save (self, filename):
		"""
			PUBLIC: save
			------------
			saves this object to disk
		"""
		pickle.dump (	{	'name':self.name,
							'image':self.image,
							'board_points': self.board_points,
							'image_points': self.image_points,
							'sift_desc':self.sift_desc,
						}, 
						open(filename, 'w'))

	
	def load (self, filename):
		"""
			PUBLIC: load
			------------
			loads a past BoardImage from a file 
		"""
		save_file 	= open(filename, 'r')
		saved_dict 	= pickle.load (save_file)
		self.name 	= saved_dict['name']
		self.image 	= saved_dict['image']
		self.board_points = saved_dict['board_points']
		self.image_points = saved_dict['image_points']
		self.sift_desc = saved_dict ['sift_desc']
		self.get_BIH ()
		self.construct_squares ()








	####################################################################################################
	##############################[ --- UTILITIES --- ]#################################################
	####################################################################################################

	def iter_squares (self):
		""" 
			PRIVATE: iter_squares
			---------------------
			iterates over all squares in this board
		"""
		for i in range(8):
			for j in range(8):
				yield self.squares [i][j]






	####################################################################################################
	##############################[ --- CV TASKS --- ]##################################################
	####################################################################################################

	def get_BIH (self):
		"""
			PRIVATE: get_BIH
			----------------
			finds the board-image homography 
		"""
		self.BIH = CVAnalysis.find_board_image_homography (self.board_points, self.image_points)


	def construct_squares (self):
		"""
			PRIVATE: construct_squares
			--------------------------
			sets self.squares
		"""
		#=====[ Step 1: initialize self.squares to empty 8x8 grid	]=====
		self.squares = [[None for i in range(8)] for j in range(8)]

		#=====[ Step 2: create a square for each algebraic notation ]=====
		for square_an in iter_algebraic_notations ():

				new_square = Square (self.image, self.BIH, square_an)
				square_location = new_square.board_vertices[0]
				self.squares [square_location[0]][square_location[1]] = new_square










	##################################################################################################
	##############################[ --- INTERFACE --- ]#################################################
	####################################################################################################

	def __str__ (self):
		"""
			PUBLIC: __str__
			---------------
			prints out the current representation of the board
		"""
		for i in range(8):
			for j in range(8):
				print self.squares[i][j].an
			print "\n"


	def print_correspondences (self):
		"""
			PUBLIC: print_correspondences
			-----------------------------
			prints out a summary of all the point correspondences 
			that we have on hand
		"""
		title 			= "==========[ 	BoardImage: " + self.name + " ]=========="
		point_count		= "##### " + str(len(self.board_points)) + " point correspondances: #####"
		point_corr 		= '\n'.join(['	' + str(bp) + '->' + str(ip) for bp, ip in zip (self.board_points, self.image_points)])
		return '\n'.join ([title, point_count, point_corr])


	def draw_squares (self, image):
		"""
			PUBLIC: draw_squares
			--------------------
			call this function to display a version of the image with square 
			outlines marked out
		"""	
		#=====[ Step 1: fill in all of the squares	]=====
		for square in self.iter_squares():
			image = square.draw_surface (image)

		#=====[ Step 2: draw them to the screen	]=====
		cv2.namedWindow ('board.draw_squares')
		cv2.imshow ('board.draw_squares', image)
		key = 0
		while key != 27:
			key = cv2.waitKey(30)


	def draw_vertices (self, draw):
		"""
			PUBLIC: draw_squares
			--------------------
			given a draw, this will draw each of the squares in self.squares
		"""
		for square in self.iter_squares ():
			square.draw_vertices (draw)



if __name__ == "__main__":
	
	board = Board (filename='test.bi')
	board.add_occlusions ('test.oc')
	X, y = board.get_occlusions ()



